"""
File parsing service for Excel and PDF sample data import.

Supports .xlsx, .xls, and .pdf.  Returns a structured ParseResult dict
so the API can report exactly what was created, updated, or failed.
"""

import io
import logging

import openpyxl
import pdfplumber

from ..models import School, Department, Lecturer, Room, TimeSlot, Course, Program, Unit, CourseUnit


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ParseResult helper
# ---------------------------------------------------------------------------

class ParseResult:
    """Accumulates counts and errors across all parsed sheets/tables."""

    def __init__(self):
        self.created = {
            "schools": 0, "departments": 0, "programs": 0,
            "lecturers": 0, "rooms": 0, "time_slots": 0,
            "courses": 0, "units": 0, "course_units": 0,
        }
        self.updated = {k: 0 for k in self.created}
        self.errors: list = []
        self.context: dict = {}  # For 'sticky' values like last-seen-day or group


    def record(self, entity: str, created: bool):
        if created:
            self.created[entity] = self.created.get(entity, 0) + 1
        else:
            self.updated[entity] = self.updated.get(entity, 0) + 1

    def add_error(self, row_info: str, exc: Exception):
        self.errors.append({"row": str(row_info), "error": str(exc)})

    def to_dict(self) -> dict:
        return {
            "created": self.created,
            "updated": self.updated,
            "error_count": len(self.errors),
            "errors": self.errors[:50],   # cap for readability
        }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

class FileParser:
    """Parses Excel and PDF files to extract and import timetable seed data."""

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    @staticmethod
    def parse_file(file, school=None) -> tuple[bool, str, dict]:
        """
        Auto-detect file type and parse accordingly.

        Args:
            file: Uploaded file object (Django InMemoryUploadedFile or similar)
            school: Optional School instance to link records to.

        Returns:
            (success, message, summary_dict)
        """
        name = (file.name or "").lower()
        if name.endswith((".xlsx", ".xls")):
            return FileParser._parse_excel(file, school)
        elif name.endswith(".pdf"):
            return FileParser._parse_pdf(file, school)
        else:
            return False, "Unsupported file type. Please upload .xlsx, .xls, or .pdf.", {}

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_excel(file, school=None) -> tuple[bool, str, dict]:
        result = ParseResult()
        try:
            wb = openpyxl.load_workbook(file, read_only=True, data_only=True)

            # Named sheet parsers (for the multi-sheet structured format)
            named_sheet_parsers = {
                "Schools":     FileParser._parse_schools_sheet,
                "Departments": FileParser._parse_departments_sheet,
                "Programs":    FileParser._parse_programs_sheet,
                "Lecturers":   FileParser._parse_lecturers_sheet,
                "Rooms":       FileParser._parse_rooms_sheet,
                "TimeSlots":   FileParser._parse_timeslots_sheet,
                "Courses":     FileParser._parse_courses_sheet,
            }

            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                # Skip instructions sheets
                if sheet_name.lower() in ("instructions", "readme", "guide", "notes"):
                    continue

                # Check if this sheet follows the flat timetable format
                # by peeking at the first data row's headers
                rows_preview = list(ws.iter_rows(min_row=1, max_row=2, values_only=True))
                if rows_preview:
                    first_row_str = " ".join([str(c or "").lower() for c in rows_preview[0]])
                    is_flat = any(k in first_row_str for k in [
                        "unit code", "unit name", "m.o.s", "course unit code", "lecturer"
                    ])

                    if is_flat:
                        FileParser._parse_flat_timetable_sheet(ws, result, school)
                    elif sheet_name in named_sheet_parsers:
                        named_sheet_parsers[sheet_name](ws, result, school)
                    else:
                        # Unknown sheet — try flat
                        FileParser._parse_flat_timetable_sheet(ws, result, school)

            total = sum(result.created.values()) + sum(result.updated.values())
            msg = (
                f"Parsed successfully: "
                f"{result.created.get('lecturers', 0)} lecturers, "
                f"{result.created.get('courses', 0)} courses, "
                f"{result.created.get('rooms', 0)} rooms, "
                f"{result.created.get('time_slots', 0)} time slots "
                f"({len(result.errors)} errors)."
            )
            return True, msg, result.to_dict()

        except Exception as exc:
            logger.exception("Excel parse error")
            return False, f"Error parsing Excel file: {exc}", {}

    @staticmethod
    def _parse_flat_timetable_sheet(ws, result: ParseResult, school=None):
        """
        Parse a flat timetable sheet with columns:
        COURSE | UNIT CODE | UNIT NAME | C.S | LECTURER | DAY | TIME | M.O.S | ROOM
        
        Also handles repeating header rows (used to separate year groups) and
        empty separator rows between groups.
        """
        import hashlib
        from ..models import StudentClass

        lnk = school or School.objects.first()
        if not lnk:
            result.add_error("Sheet", Exception("No school found. Create a school first."))
            return

        # Detect column positions from the first header row
        FLAT_HEADERS = {
            "course":     ["course"],
            "unit_code":  ["unit code", "code"],
            "unit_name":  ["unit name", "name"],
            "class_size": ["c.s", "cs", "class size", "size"],
            "lecturer":   ["lecturer", "staff"],
            "day":        ["day"],
            "time":       ["time"],
            "mos":        ["m.o.s", "mos", "mode"],
            "room":       ["room"],
        }

        col_map = {}  # key -> 0-based column index

        def detect_col_map(header_row):
            """Map column names from a header row."""
            cmap = {}
            for i, cell in enumerate(header_row):
                h = str(cell or "").lower().strip()
                for key, candidates in FLAT_HEADERS.items():
                    if any(c in h for c in candidates):
                        if key not in cmap:
                            cmap[key] = i
            return cmap

        def norm_t(t):
            """Normalize a time string like 7:00AM or 4:00PM to HH:MM."""
            if not t: return "08:00"
            t = str(t).lower().strip()
            is_pm = "pm" in t
            t = t.replace("am", "").replace("pm", "").strip()
            if ":" not in t:
                t = t + ":00"
            try:
                h, m = map(int, t.split(":")[:2])
                if is_pm and h < 12: h += 12
                if not is_pm and h == 12: h = 0
                return f"{h:02d}:{m:02d}"
            except Exception:
                return "08:00"

        def parse_time_range(time_str):
            """Parse '7:00AM-10:00AM' into (start, end)."""
            if not time_str:
                return "08:00", "11:00"
            time_str = str(time_str)
            # Support dash and en-dash
            for sep in ["-", "–", "to"]:
                if sep in time_str:
                    parts = time_str.split(sep, 1)
                    return norm_t(parts[0]), norm_t(parts[1])
            return norm_t(time_str), "11:00"

        def get_col(row, key):
            i = col_map.get(key, -1)
            if i < 0 or i >= len(row):
                return None
            v = row[i]
            return str(v).strip() if v is not None else None

        # ── Iterate rows ──────────────────────────────────────────────────────
        last_group = None
        last_day   = None

        for row in ws.iter_rows(values_only=True):
            if all(c is None or str(c).strip() == "" for c in row):
                continue  # Empty separator row

            row_str = " ".join([str(c or "").lower() for c in row])

            # Auto-detect header rows (re-detect column map on each header)
            if any(k in row_str for k in ["unit code", "unit name", "lecturer", "m.o.s"]):
                col_map = detect_col_map(row)
                continue  # Header row, not data

            if not col_map:
                col_map = detect_col_map(row)
                continue

            # ── Extract fields ────────────────────────────────────────────────
            group_raw     = get_col(row, "course")
            unit_code     = get_col(row, "unit_code")
            unit_name     = get_col(row, "unit_name")
            class_size    = int(get_col(row, "class_size") or 0)
            lecturer_name = get_col(row, "lecturer")
            day           = get_col(row, "day")
            time_raw      = get_col(row, "time")
            room_name     = get_col(row, "room")

            # Sticky context
            if group_raw: last_group = group_raw
            if day:       last_day   = day

            # Skip if we don't have basic subject/lecturer/time info
            if not all([unit_name or unit_code, lecturer_name, last_day, time_raw]):
                continue

            try:
                # ── HIERARCHY: Course (Group/Year) ───────────────────────────
                # In the new hierarchy, Course = "BIT Y1 S2"
                course_code = str(last_group).upper().replace(" ", "-") if last_group else "AUTO-GRP"
                
                # Try to guess department from course code (e.g. BIT -> CS)
                dept_code = course_code.split('-')[0][:4]
                dept, _ = Department.objects.get_or_create(
                    code=dept_code, school=lnk,
                    defaults={"name": f"{dept_code} Department"}
                )

                course, c_created = Course.objects.get_or_create(
                    code=course_code, department=dept,
                    defaults={"name": str(last_group or "Auto Course"), "semester": 1}
                )
                result.record("courses", c_created)

                # ── HIERARCHY: Unit (Subject) ───────────────────────────────
                u_code = unit_code or (unit_name[:8].replace(" ", "") if unit_name else "UNK")
                unit, u_created = Unit.objects.get_or_create(
                    code=u_code,
                    defaults={"name": unit_name or u_code, "credits": 3, "hours_per_week": 3}
                )
                result.record("units", u_created)

                # Link Unit to Course
                _, cu_created = CourseUnit.objects.get_or_create(
                    unit=unit, course=course,
                    defaults={"year_of_study": 1, "semester": 1}
                )
                result.record("course_units", cu_created)

                # ── LECTURER ─────────────────────────────────────────────────
                name_hash = hashlib.sha1(lecturer_name.encode("utf-8")).hexdigest()[:8].upper()
                emp_id = f"LEC-{name_hash}"
                parts = lecturer_name.strip().split()
                first, last = parts[0], " ".join(parts[1:]) if len(parts) > 1 else ""
                email = f"{emp_id.lower()}@school.edu"
                lecturer, lec_created = Lecturer.objects.update_or_create(
                    employee_id=emp_id, school=lnk,
                    defaults={"first_name": first, "last_name": last, "email": email, "department": dept}
                )
                result.record("lecturers", lec_created)

                # ── ROOM ─────────────────────────────────────────────────────
                rtype = "online" if any(x in str(room_name or "").lower() for x in ["zoom", "online"]) else "lecture"
                room, r_created = Room.objects.get_or_create(
                    school=lnk, room_number=str(room_name or "TBA"),
                    defaults={"building": "Main", "capacity": max(class_size, 30), "room_type": rtype}
                )
                result.record("rooms", r_created)

                # ── TIME SLOT ────────────────────────────────────────────────
                start_str, end_str = parse_time_range(time_raw)
                day_3 = str(last_day).upper()[:3]
                timeslot, ts_created = TimeSlot.objects.get_or_create(
                    school=lnk, day=day_3, start_time=start_str, end_time=end_str,
                    defaults={"slot_name": f"{day_3} {start_str}-{end_str}"}
                )
                result.record("time_slots", ts_created)

            except Exception as exc:
                result.add_error(f"Row: {row}", exc)


    # Sheet parsers ---------------------------------------------------------

    @staticmethod
    def _parse_schools_sheet(ws, result: ParseResult, school=None):
        for row in ws.iter_rows(min_row=2, values_only=True):
            name, code, desc = (row[0], row[1] if len(row) > 1 else None, row[2] if len(row) > 2 else "")
            if not name:
                continue
            try:
                code = str(code or name[:4]).upper().strip()
                obj, created = School.objects.get_or_create(
                    code=code,
                    defaults={"name": str(name), "description": str(desc or "")},
                )
                result.record("schools", created)
            except Exception as exc:
                result.add_error(f"School row: {row}", exc)

    @staticmethod
    def _parse_departments_sheet(ws, result: ParseResult, school=None):
        for row in ws.iter_rows(min_row=2, values_only=True):
            name, code = row[0], row[1] if len(row) > 1 else None
            if not name:
                continue
            try:
                code = str(code or name[:4]).upper().strip()
                linked_school = school
                if linked_school is None:
                    school_code = row[2] if len(row) > 2 else None
                    if school_code:
                        linked_school = School.objects.filter(code=str(school_code)).first()
                    if linked_school is None:
                        linked_school = School.objects.first()
                if linked_school is None:
                    result.add_error(f"Dept {name}", Exception("No school found. Create a school first."))
                    continue
                obj, created = Department.objects.get_or_create(
                    code=code,
                    school=linked_school,
                    defaults={"name": str(name)},
                )
                result.record("departments", created)
            except Exception as exc:
                result.add_error(f"Department row: {row}", exc)

    @staticmethod
    def _parse_programs_sheet(ws, result: ParseResult, school=None):
        for row in ws.iter_rows(min_row=2, values_only=True):
            name, code = row[0], row[1] if len(row) > 1 else None
            if not name:
                continue
            try:
                code = str(code or name[:4]).upper().strip()
                dept_code = row[2] if len(row) > 2 else None
                level = str(row[3]) if len(row) > 3 and row[3] else "100"
                dept = Department.objects.filter(code=str(dept_code)).first() if dept_code else Department.objects.first()
                if dept is None:
                    result.add_error(f"Program {name}", Exception("No department found"))
                    continue
                obj, created = Program.objects.get_or_create(
                    code=code,
                    department=dept,
                    defaults={"name": str(name), "level": level},
                )
                result.record("programs", created)
            except Exception as exc:
                result.add_error(f"Program row: {row}", exc)

    @staticmethod
    def _parse_lecturers_sheet(ws, result: ParseResult, school=None):
        for row in ws.iter_rows(min_row=2, values_only=True):
            name = row[0]
            if not name:
                continue
            try:
                emp_id = str(row[1]) if len(row) > 1 and row[1] else f"EMP-{str(name)[:4].upper()}"
                dept_code = row[2] if len(row) > 2 else None
                email = str(row[3]) if len(row) > 3 and row[3] else f"{emp_id.lower()}@school.edu"
                title = str(row[4]) if len(row) > 4 and row[4] else ""

                dept = Department.objects.filter(code=str(dept_code)).first() if dept_code else Department.objects.first()
                lnk_school = school or (dept.school if dept else School.objects.first())
                if lnk_school is None:
                    result.add_error(f"Lecturer {name}", Exception("No school found"))
                    continue

                # Split name
                parts = str(name).strip().split()
                first = parts[0] if parts else str(name)
                last = " ".join(parts[1:]) if len(parts) > 1 else ""

                obj, created = Lecturer.objects.get_or_create(
                    employee_id=emp_id,
                    school=lnk_school,
                    defaults={
                        "first_name": first,
                        "last_name": last,
                        "email": email,
                        "title": title,
                        "department": dept,
                    },
                )
                result.record("lecturers", created)
            except Exception as exc:
                result.add_error(f"Lecturer row: {row}", exc)

    @staticmethod
    def _parse_rooms_sheet(ws, result: ParseResult, school=None):
        for row in ws.iter_rows(min_row=2, values_only=True):
            room_number = row[0]
            if not room_number:
                continue
            try:
                building = str(row[1]) if len(row) > 1 and row[1] else "Main"
                capacity = int(row[2]) if len(row) > 2 and row[2] else 30
                room_type = str(row[3]).lower() if len(row) > 3 and row[3] else "lecture"
                lnk_school = school or School.objects.first()
                if lnk_school is None:
                    result.add_error(f"Room {room_number}", Exception("No school found"))
                    continue

                obj, created = Room.objects.get_or_create(
                    school=lnk_school,
                    building=building,
                    room_number=str(room_number),
                    defaults={"capacity": capacity, "room_type": room_type},
                )
                result.record("rooms", created)
            except Exception as exc:
                result.add_error(f"Room row: {row}", exc)

    @staticmethod
    def _parse_timeslots_sheet(ws, result: ParseResult, school=None):
        for row in ws.iter_rows(min_row=2, values_only=True):
            day, start, end = row[0], row[1] if len(row) > 1 else None, row[2] if len(row) > 2 else None
            if not (day and start and end):
                continue
            try:
                lnk_school = school or School.objects.first()
                if lnk_school is None:
                    result.add_error(f"TimeSlot {row}", Exception("No school found"))
                    continue
                slot_name = str(row[3]) if len(row) > 3 and row[3] else ""
                obj, created = TimeSlot.objects.get_or_create(
                    school=lnk_school,
                    day=str(day).upper()[:3],
                    start_time=str(start),
                    end_time=str(end),
                    defaults={"slot_name": slot_name},
                )
                result.record("time_slots", created)
            except Exception as exc:
                result.add_error(f"TimeSlot row: {row}", exc)

    @staticmethod
    def _parse_courses_sheet(ws, result: ParseResult, school=None):
        for row in ws.iter_rows(min_row=2, values_only=True):
            code, name = row[0], row[1] if len(row) > 1 else None
            if not (code and name):
                continue
            try:
                prog_code = row[2] if len(row) > 2 else None
                credits = int(row[3]) if len(row) > 3 and row[3] else 3
                semester = int(row[4]) if len(row) > 4 and row[4] else 1

                program = Program.objects.filter(code=str(prog_code)).first() if prog_code else Program.objects.first()
                if program is None:
                    result.add_error(f"Course {code}", Exception(f"Program '{prog_code}' not found"))
                    continue

                obj, created = Course.objects.get_or_create(
                    code=str(code),
                    program=program,
                    defaults={
                        "name": str(name),
                        "credits": max(1, min(credits, 10)),
                        "semester": max(1, min(semester, 8)),
                    },
                )
                result.record("courses", created)
            except Exception as exc:
                result.add_error(f"Course row: {row}", exc)

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_pdf(file, school=None) -> tuple[bool, str, dict]:
        result = ParseResult()
        try:
            with pdfplumber.open(file) as pdf:
                all_tables = []
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() or ""
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)

            if all_tables:
                FileParser._parse_pdf_tables(all_tables, result, school)
            else:
                FileParser._parse_pdf_text(full_text, result, school)

            msg = (
                f"PDF parsed: "
                f"{result.created['departments']} depts, "
                f"{result.created['lecturers']} lecturers, "
                f"{result.created['rooms']} rooms, "
                f"{result.created['courses']} courses "
                f"({len(result.errors)} errors)."
            )
            return True, msg, result.to_dict()
        except Exception as exc:
            logger.exception("PDF parse error")
            return False, f"Error parsing PDF: {exc}", {}

    @staticmethod
    def _parse_pdf_tables(tables, result: ParseResult, school=None):
        """Identify tables by header keywords and route to appropriate parser."""
        for table in tables:
            if not table or len(table) < 2:
                continue
                
            # Filter out empty rows and normalize header
            rows = [row for row in table if any(cell is not None and str(cell).strip() for cell in row)]
            if not rows:
                continue
                
            header_row = [str(h or "").lower().strip() for h in rows[0]]
            header_str = " ".join(header_row)

            # Map headers to upsert functions
            # 1. Check for specific headers
            if any(k in header_str for k in ["unit code", "unit name", "m.o.s", "course unit code"]):
                for row in rows[1:]:
                    FileParser._upsert_flat_row(row, result, school)
            elif any(k in header_str for k in ["dept", "department"]):
                for row in rows[1:]:
                    FileParser._upsert_department(row, result, school)
            elif any(k in header_str for k in ["lecturer", "staff", "teacher"]):
                for row in rows[1:]:
                    FileParser._upsert_lecturer(row, result, school)
            elif "room" in header_str:
                for row in rows[1:]:
                    FileParser._upsert_room(row, result, school)
            elif any(k in header_str for k in ["time", "slot"]):
                for row in rows[1:]:
                    FileParser._upsert_timeslot(row, result, school)
            elif any(k in header_str for k in ["course", "unit", "subject"]):
                for row in rows[1:]:
                    FileParser._upsert_course(row, result, school)
            elif any(k in header_str for k in ["school", "institution"]):
                for row in rows[1:]:
                    FileParser._upsert_school(row, result, school)
            else:
                # 2. Fallback: Check if rows look like a flat timetable (Day + Time detection)
                # Look at first few rows to see if they contain a day like MONDAY
                days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
                session_like = False
                for row in rows[:3]:
                    row_str = " ".join([str(c or "").upper() for c in row])
                    if any(d in row_str for d in days) and any(x in row_str for x in [":", "00", "30"]):
                        session_like = True
                        break
                
                if session_like:
                    for row in rows: # Include first row if it was actually data
                        FileParser._upsert_flat_row(row, result, school)

    @staticmethod
    def _parse_pdf_text(text: str, result: ParseResult, school=None):
        """Fallback: try to find department names from raw text."""
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2 and len(parts[-1]) <= 6 and parts[-1].isupper():
                code = parts[-1]
                name = " ".join(parts[:-1])
                try:
                    lnk_school = school or School.objects.first()
                    if lnk_school:
                        _, created = Department.objects.get_or_create(
                            code=code, school=lnk_school, defaults={"name": name}
                        )
                        result.record("departments", created)
                except Exception as exc:
                    result.add_error(line, exc)

    # ------------------------------------------------------------------
    # Row-level upsert helpers (used by PDF table parser)
    # ------------------------------------------------------------------

    @staticmethod
    def _upsert_school(row, result, _unused_school):
        try:
            name = FileParser._get_val(row, 0)
            if not name: return
            code = FileParser._get_val(row, 1) or name[:4].upper()
            desc = FileParser._get_val(row, 2) or ""
            _, created = School.objects.get_or_create(
                code=code.strip().upper(),
                defaults={"name": name, "description": desc}
            )
            result.record("schools", created)
        except Exception as exc:
            result.add_error(row, exc)

    @staticmethod
    def _upsert_department(row, result, school):
        try:
            name = FileParser._get_val(row, 0)
            if not name: return
            code = FileParser._get_val(row, 1) or name[:4].upper()
            lnk = school or School.objects.first()
            if not lnk:
                result.add_error(row, Exception("No school found to link department to"))
                return
            _, created = Department.objects.get_or_create(
                code=code.strip().upper(), school=lnk, defaults={"name": name}
            )
            result.record("departments", created)
        except Exception as exc:
            result.add_error(row, exc)

    @staticmethod
    def _upsert_lecturer(row, result, school):
        try:
            name = FileParser._get_val(row, 0)
            if not name: return
            
            # Generate a more unique employee_id to avoid collisions (D7 fix)
            # Use provided ID if available, otherwise hash the name
            raw_id = FileParser._get_val(row, 1)
            if raw_id:
                emp_id = raw_id
            else:
                import hashlib
                name_hash = hashlib.sha1(name.encode('utf-8')).hexdigest()[:8].upper()
                emp_id = f"LEC-{name_hash}"

            dept_code = FileParser._get_val(row, 2)
            dept = Department.objects.filter(code=dept_code).first() if dept_code else Department.objects.first()
            lnk = school or (dept.school if dept else School.objects.first())
            if not lnk:
                result.add_error(row, Exception("No school found for lecturer"))
                return
            
            parts = name.strip().split()
            first, last = parts[0], " ".join(parts[1:]) if len(parts) > 1 else ""
            
            # Use emp_id to make email unique (D7 fix)
            email = FileParser._get_val(row, 3) or f"{emp_id.lower()}@school.edu"
            
            _, created = Lecturer.objects.update_or_create(
                employee_id=emp_id, school=lnk,
                defaults={"first_name": first, "last_name": last, "email": email, "department": dept},
            )
            result.record("lecturers", created)
        except Exception as exc:
            result.add_error(row, exc)

    @staticmethod
    def _upsert_room(row, result, school):
        try:
            room_number = FileParser._get_val(row, 0)
            if not room_number: return
            building = FileParser._get_val(row, 1) or "Main"
            capacity = int(FileParser._get_val(row, 2) or 30)
            room_type = str(FileParser._get_val(row, 3) or "lecture").lower()
            lnk = school or School.objects.first()
            if not lnk: return
            _, created = Room.objects.get_or_create(
                school=lnk, building=building, room_number=str(room_number),
                defaults={"capacity": capacity, "room_type": room_type},
            )
            result.record("rooms", created)
        except Exception as exc:
            result.add_error(row, exc)

    @staticmethod
    def _upsert_timeslot(row, result, school):
        try:
            day_raw = FileParser._get_val(row, 0)
            if not day_raw: return
            day = str(day_raw).upper()[:3]
            start = FileParser._get_val(row, 1) or "08:00"
            end = FileParser._get_val(row, 2) or "09:00"
            lnk = school or School.objects.first()
            if not lnk: return
            _, created = TimeSlot.objects.get_or_create(
                school=lnk, day=day, start_time=start, end_time=end,
                defaults={"slot_name": FileParser._get_val(row, 3) or ""},
            )
            result.record("time_slots", created)
        except Exception as exc:
            result.add_error(row, exc)

    @staticmethod
    def _upsert_course(row, result, school):
        try:
            code = FileParser._get_val(row, 0)
            if not code: return
            name = FileParser._get_val(row, 1) or code
            dept_code = FileParser._get_val(row, 2)
            semester = int(FileParser._get_val(row, 4) or 1)
            
            lnk = school or School.objects.first()
            dept = Department.objects.filter(code=dept_code).first() if dept_code else Department.objects.filter(school=lnk).first()
            if not dept:
                # Create a fallback dept if none exists
                dept, _ = Department.objects.get_or_create(code="AUTO", school=lnk, defaults={"name": "Auto Dept"})

            _, created = Course.objects.get_or_create(
                code=code, department=dept,
                defaults={"name": name, "semester": max(1, min(semester, 8))},
            )
            result.record("courses", created)
        except Exception as exc:
            result.add_error(row, exc)

        except Exception as exc:
            result.add_error(row, exc)

    @staticmethod
    def _upsert_flat_row(row, result, school):
        """
        Supports a flat row containing multiple entities.
        Tries to adapt to different layouts.
        """
        try:
            row_str = " ".join([str(c or "").upper() for c in row])
            if not any(d in row_str for d in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
                return # Skip non-data rows

            lnk = school or School.objects.first()
            if not lnk: return

            # Adaptive index picking
            # Format A (user expected): COURSE, CODE, NAME, CS, LEC, DAY, TIME, MOS, ROOM
            # Format B (error log): COURSE, ROOM, LEC, MOS, TIME, SIZE, SIZE, LEVEL
            
            day_idx = -1
            time_idx = -1
            days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
            
            # Find Day and Time columns first
            for i, val in enumerate(row):
                v = str(val or "").upper()
                if any(d in v for d in days): day_idx = i
                if ":" in v or ("AM" in v or "PM" in v): time_idx = i

            if day_idx == -1 or time_idx == -1:
                return

            # Derive other fields relative to day/time
            if day_idx > 3: # Format A-ish
                prog_info = FileParser._get_val(row, 0)
                course_code = FileParser._get_val(row, 1)
                course_name = FileParser._get_val(row, 2)
                class_size = int(FileParser._get_val(row, 3) or 0)
                lecturer_name = FileParser._get_val(row, 4)
                room_name = FileParser._get_val(row, 8) if len(row) > 8 else FileParser._get_val(row, day_idx+3)
            else: # Format B-ish
                course_name = FileParser._get_val(row, 0)
                course_code = course_name[:8].replace(" ","") if course_name else "UNK"
                room_name = FileParser._get_val(row, 1)
                lecturer_name = FileParser._get_val(row, 2)
                prog_info = FileParser._get_val(row, len(row)-1) # Year/Level usually at end
                class_size = int(FileParser._get_val(row, day_idx+2) or 0)

            if day_idx != -1:
                result.context['last_day'] = row[day_idx]
            
            day = row[day_idx] if day_idx != -1 else result.context.get('last_day')
            time_raw = row[time_idx] if time_idx != -1 else None
            
            if not all([course_name, lecturer_name, day]):
                return

            lnk = school or School.objects.first()
            if not lnk: return

            # UPSERT LECTURER
            FileParser._upsert_lecturer([lecturer_name, None, None, None], result, lnk)
            lecturer = Lecturer.objects.filter(school=lnk).order_by('-id').first() # Get last worked on or match name
            # Better match for lecturer:
            import hashlib
            name_hash = hashlib.sha1(lecturer_name.encode('utf-8')).hexdigest()[:8].upper()
            lecturer = Lecturer.objects.get(employee_id=f"LEC-{name_hash}", school=lnk)

            # UPSERT HIERARCHY
            # Course = Group
            # Unit = Subject
            group_code = str(prog_info).upper().replace(" ", "-") if prog_info else "AUTO-GRP"
            dept = Department.objects.filter(school=lnk).first() or Department.objects.create(code="AUTO", name="Auto Dept", school=lnk)
            
            course, c_created = Course.objects.get_or_create(
                code=group_code, department=dept, 
                defaults={"name": str(prog_info or "Auto Course")}
            )
            result.record("courses", c_created)

            u_code = course_code or (course_name[:8].replace(" ", "") if course_name else "UNK")
            unit, u_created = Unit.objects.get_or_create(
                code=u_code,
                defaults={"name": course_name or u_code, "credits": 3}
            )
            result.record("units", u_created)

            # Link Unit to Course
            CourseUnit.objects.get_or_create(unit=unit, course=course)
            result.record("course_units", 1)

            # UPSERT ROOM
            room, created = Room.objects.get_or_create(
                school=lnk, room_number=str(room_name or "TBA"),
                defaults={"building": "Main", "capacity": max(class_size, 30), "room_type": "lecture"}
            )
            result.record("rooms", created)

            # UPSERT TIME SLOT
            start_str, end_str = "08:00", "11:00"
            if "-" in str(time_raw):
                parts = str(time_raw).split("-")
                start_str, end_str = parts[0].strip(), parts[1].strip()
            
            # Simple normalization for 7:00AM -> 07:00
            def norm_t(t):
                if not t: return "08:00"
                t = str(t).lower().strip()
                is_pm = "pm" in t
                t = t.replace("am", "").replace("pm", "").strip()
                if ":" not in t: t = t + ":00"
                try:
                    h, m = map(int, t.split(":")[:2])
                    if is_pm and h < 12: h += 12
                    if not is_pm and h == 12: h = 0
                    return f"{h:02d}:{m:02d}"
                except: return "08:00"
            
            timeslot, created = TimeSlot.objects.get_or_create(
                school=lnk, day=str(day).upper()[:3],
                start_time=norm_t(start_str), end_time=norm_t(end_str),
                defaults={"slot_name": f"{start_str}-{end_str}"}
            )
            result.record("time_slots", created)

            
        except Exception as exc:
            result.add_error(row, exc)

    @staticmethod
    def _get_val(row, index, default=None):
        if len(row) > index and row[index] is not None:
            val = str(row[index]).strip()
            return val if val else default
        return default

    # ------------------------------------------------------------------
    # Legacy compatibility shims (used by older views)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_training_data_file(file, school=None):
        """Alias for parse_file — kept for backward compatibility."""
        ok, msg, summary = FileParser.parse_file(file, school)
        return ok, msg, summary
