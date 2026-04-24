"""
Constraint-based timetable scheduler using OR-Tools CP-SAT.

ML optimizer scores are used as a soft objective to prefer historically
good (course, time_slot, room) assignments while hard constraints (no
double-bookings, capacity, availability) are always enforced.
"""

import logging
from ortools.sat.python import cp_model
from ..models import TimetableEntry, LecturerAvailability

logger = logging.getLogger(__name__)

# Score scale: ML scores [0,1] are multiplied by this to create integer
# coefficients for the OR-Tools objective.
SCORE_SCALE = 100


class TimetableScheduler:
    """
    Manages automated timetable generation using constraint programming.

    Hard constraints:
    - Each course scheduled exactly once
    - No room double-bookings
    - No lecturer double-bookings
    - Room capacity >= course student count
    - Respect lecturer unavailability windows

    Soft objective (maximised):
    - ML-predicted quality scores for each assignment
    """

    def __init__(self, courses, lecturers, rooms, time_slots,
                 timetable=None, ml_optimizer=None):
        self.courses = list(courses)
        self.lecturers = list(lecturers)
        self.rooms = list(rooms)
        self.time_slots = list(time_slots)
        self.timetable = timetable
        self.ml_optimizer = ml_optimizer

        self.model = cp_model.CpModel()
        self.variables = {}          # [c_idx][t_idx][r_idx] -> BoolVar
        self.lecturer_course_map = {}  # c_idx -> Lecturer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self):
        """
        Generate an optimised timetable.

        Returns:
            list[TimetableEntry]: created entry objects, or [] if no solution found
        """
        if not self.courses:
            raise ValueError("No courses to schedule.")
        if not self.rooms:
            raise ValueError("No rooms available.")
        if not self.time_slots:
            raise ValueError("No time slots available.")
        if not self.lecturers:
            raise ValueError("No lecturers available.")

        try:
            self._build_lecturer_map()
            self._create_decision_variables()
            self._add_mandatory_constraints()
            self._add_resource_constraints()
            self._add_availability_constraints()
            self._add_ml_objective()
            return self._solve_and_create_entries()
        except Exception as exc:
            logger.exception("Scheduling failed")
            raise ValueError(f"Scheduling failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _build_lecturer_map(self):
        """
        Assign one lecturer per course.
        Logic:
        1. Prefer lecturer in course.department
        2. Fallback: lecturer in course.program.department
        3. Fallback: any available lecturer
        """
        self.lecturer_course_map = {}
        for c_idx, course in enumerate(self.courses):
            dept_id = course.department_id
            if not dept_id and course.program:
                dept_id = course.program.department_id

            lecturer = next(
                (l for l in self.lecturers
                 if l.department_id == dept_id and l.is_available),
                None
            )
            if lecturer is None:
                # Last resort Fallback: any available lecturer
                lecturer = next((l for l in self.lecturers if l.is_available), None)

            if lecturer:
                self.lecturer_course_map[c_idx] = lecturer


        if not self.lecturer_course_map:
            raise ValueError("No lecturer could be assigned to any course.")

    def _create_decision_variables(self):
        """Boolean var: course c assigned to time t in room r."""
        for c_idx in range(len(self.courses)):
            self.variables[c_idx] = {}
            for t_idx in range(len(self.time_slots)):
                self.variables[c_idx][t_idx] = {}
                for r_idx in range(len(self.rooms)):
                    name = f"c{c_idx}_t{t_idx}_r{r_idx}"
                    self.variables[c_idx][t_idx][r_idx] = self.model.NewBoolVar(name)

    def _add_mandatory_constraints(self):
        """Each course exactly once; no room double-booking."""
        # Each course scheduled exactly once
        for c_idx in range(len(self.courses)):
            all_vars = [
                self.variables[c_idx][t_idx][r_idx]
                for t_idx in range(len(self.time_slots))
                for r_idx in range(len(self.rooms))
            ]
            self.model.Add(sum(all_vars) == 1)

        # No two courses in the same room at the same time
        for t_idx in range(len(self.time_slots)):
            for r_idx in range(len(self.rooms)):
                room_vars = [self.variables[c_idx][t_idx][r_idx]
                             for c_idx in range(len(self.courses))]
                self.model.Add(sum(room_vars) <= 1)

    def _add_resource_constraints(self):
        """Room capacity and lecturer double-booking constraints."""
        from ..models import StudentClass
        
        # Room too small → forbidden
        # Pre-fetch student class sizes for all courses to avoid DB calls in loops
        # Room too small → forbidden
        # Pre-fetch student class sizes for all courses to avoid DB calls in loops
        class_sizes = {
            (sc.course_id, sc.program_id): sc.student_count 
            for sc in StudentClass.objects.filter(course__in=self.courses)
        }


        for c_idx, course in enumerate(self.courses):
            # Look up student count for this specific course in its program
            class_size = class_sizes.get((course.id, course.program_id), 0)
            
            for t_idx in range(len(self.time_slots)):
                for r_idx, room in enumerate(self.rooms):
                    if room.capacity < class_size:
                        self.model.Add(self.variables[c_idx][t_idx][r_idx] == 0)

        # Each lecturer at most one course per time slot
        for lecturer in set(self.lecturer_course_map.values()):
            courses_for = [c_idx for c_idx, l in self.lecturer_course_map.items() if l == lecturer]
            for t_idx in range(len(self.time_slots)):
                lec_vars = [
                    self.variables[c_idx][t_idx][r_idx]
                    for c_idx in courses_for
                    for r_idx in range(len(self.rooms))
                ]
                if lec_vars:
                    self.model.Add(sum(lec_vars) <= 1)

    def _add_availability_constraints(self):
        """Block slots where a lecturer is marked unavailable."""
        unavailable = list(LecturerAvailability.objects.filter(is_available=False)
                           .select_related('lecturer'))

        for avail in unavailable:
            # Match by day + time overlap
            blocked_t_idxs = [
                t_idx for t_idx, ts in enumerate(self.time_slots)
                if (ts.day == avail.day
                    and ts.start_time >= avail.start_time
                    and ts.start_time < avail.end_time)
            ]
            for c_idx, lecturer in self.lecturer_course_map.items():
                if lecturer.id == avail.lecturer.id:
                    for t_idx in blocked_t_idxs:
                        for r_idx in range(len(self.rooms)):
                            self.model.Add(self.variables[c_idx][t_idx][r_idx] == 0)

    def _add_ml_objective(self):
        """Add a maximise objective based on ML quality scores."""
        if self.ml_optimizer is None:
            return

        terms = []
        for c_idx, course in enumerate(self.courses):
            for t_idx, ts in enumerate(self.time_slots):
                for r_idx, room in enumerate(self.rooms):
                    raw_score = self.ml_optimizer.score(
                        day=ts.day,
                        start_time=ts.start_time,
                        room=room,
                        course=course,
                    )
                    int_score = int(raw_score * SCORE_SCALE)
                    if int_score > 0:
                        terms.append(self.variables[c_idx][t_idx][r_idx] * int_score)

        if terms:
            self.model.Maximize(sum(terms))

    def _solve_and_create_entries(self):
        """Run the solver and persist TimetableEntry objects."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0   # safety timeout

        status = solver.Solve(self.model)
        logger.info("Solver status: %s", solver.StatusName(status))

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.warning("No feasible solution found (status=%s)", status)
            return []

        entries = []
        for c_idx, course in enumerate(self.courses):
            for t_idx, time_slot in enumerate(self.time_slots):
                for r_idx, room in enumerate(self.rooms):
                    if solver.Value(self.variables[c_idx][t_idx][r_idx]):
                        lecturer = self.lecturer_course_map.get(c_idx)
                        if not lecturer:
                            continue

                        kwargs = dict(
                            course=course,
                            lecturer=lecturer,
                            room=room,
                            day=time_slot.day,
                            start_time=time_slot.start_time,
                            end_time=time_slot.end_time,
                            duration_hours=(
                                (time_slot.end_time.hour * 60 + time_slot.end_time.minute
                                 - time_slot.start_time.hour * 60 - time_slot.start_time.minute) / 60
                            ),
                        )
                        if self.timetable:
                            kwargs['timetable'] = self.timetable

                        # Provide a dummy student_class if none given
                        # (required by the model's NOT NULL constraint)
                        from ..models import StudentClass
                        student_class = StudentClass.objects.filter(
                            course=course
                        ).first()
                        if student_class is None:
                            # Create a minimal one so we can save
                            program = course.program
                            # Use course.department's first program if course.program is null
                            if not program and course.department:
                                from ..models import Program
                                program = Program.objects.filter(department=course.department).first()
                            
                            student_class, _ = StudentClass.objects.get_or_create(
                                program=program,  # might still be null if no program exists at all
                                course=course,
                                class_name=f"{course.code} Auto",
                                semester=course.semester,
                                academic_year="2024/2025",
                                defaults={"student_count": getattr(course, 'class_size', 1) or 1},
                            )
                        kwargs['student_class'] = student_class


                        entry = TimetableEntry.objects.create(**kwargs)
                        entries.append(entry)

        logger.info("Created %d timetable entries", len(entries))
        return entries
