"""
ITC XML to JSON Converter
Converts International Timetabling Competition XML format to standardized JSON schema
for ML training and backend ingestion.

Schema mapping:
  ITC Rooms     → backend Rooms
  ITC Courses   → backend Courses (with Configs → Lectures/Class sessions)
  ITC Students  → backend Students (enrolled in Courses)
  ITC Distributions → Constraints
"""

import xml.etree.ElementTree as ET
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ITCXMLConverter:
    """Convert ITC XML timetable format to standardized JSON."""
    
    def __init__(self):
        """Initialize converter."""
        self.problem_meta = {}
        self.rooms_map = {}
        self.courses_map = {}
        self.students_map = {}
        self.timeslots = []
        self.constraints = []
    
    def parse_xml(self, xml_file: str) -> ET.Element:
        """Parse XML file safely."""
        try:
            tree = ET.parse(xml_file)
            return tree.getroot()
        except ET.ParseError as e:
            logger.error(f"Failed to parse {xml_file}: {e}")
            raise
    
    def extract_problem_meta(self, root: ET.Element) -> Dict[str, Any]:
        """
        Extract problem metadata (days, weeks, slots, optimization weights).
        
        Returns:
            Dict with problem configuration
        """
        meta = {
            "problem_name": root.attrib.get('name', 'unknown'),
            "nr_days": int(root.attrib.get('nrDays', 5)),  # Mon-Fri typically
            "nr_weeks": int(root.attrib.get('nrWeeks', 1)),
            "slots_per_day": int(root.attrib.get('slotsPerDay', 48)),  # 30-min slots throughout day
            "optimization_weights": {}
        }
        
        opt = root.find('optimization')
        if opt is not None:
            meta["optimization_weights"] = {
                "time": float(opt.attrib.get('time', 4)),
                "room": float(opt.attrib.get('room', 1)),
                "distribution": float(opt.attrib.get('distribution', 15)),
                "student": float(opt.attrib.get('student', 5))
            }
        
        self.problem_meta = meta
        logger.info(f"Problem: {meta['problem_name']}")
        logger.info(f"  Days: {meta['nr_days']}, Weeks: {meta['nr_weeks']}, Slots/day: {meta['slots_per_day']}")
        
        return meta
    
    def extract_rooms(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Convert ITC rooms to standardized format.
        
        ITC format: <room id="1" capacity="50">
                      <travel room="2" value="5"/>  <!-- travel time between rooms -->
                    </room>
        """
        rooms = []
        rooms_elem = root.find('rooms')
        
        if rooms_elem is None:
            logger.warning("No rooms found in XML")
            return rooms
        
        for room_elem in rooms_elem:
            room_id = room_elem.attrib.get('id')
            capacity = int(room_elem.attrib.get('capacity', 100))
            
            travel_times = {}
            for travel in room_elem.findall('travel'):
                travel_room_id = travel.attrib.get('room')
                travel_time = int(travel.attrib.get('value', 0))
                travel_times[travel_room_id] = travel_time
            
            room = {
                "id": room_id,
                "name": f"Room-{room_id}",
                "capacity": capacity,
                "building": "Main",  # Not in ITC format, use default
                "room_type": "Classroom",  # Not specified in ITC
                "travel_times": travel_times
            }
            rooms.append(room)
            self.rooms_map[room_id] = room
        
        logger.info(f"Extracted {len(rooms)} rooms")
        return rooms
    
    def extract_timeslots(self) -> List[Dict[str, Any]]:
        """
        Generate time slots from problem metadata.
        
        ITC format: Defines days, weeks, and slots per day.
        Creates time slots in 30-minute intervals.
        """
        timeslots = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][:self.problem_meta['nr_days']]
        
        slot_duration_minutes = 30  # Standard ITC slot duration
        slots_per_day = self.problem_meta['slots_per_day']
        minutes_per_day = slots_per_day * slot_duration_minutes
        
        slot_id = 1
        for week in range(1, self.problem_meta['nr_weeks'] + 1):
            for day_idx, day_name in enumerate(days):
                current_time = 480  # 8:00 AM in minutes
                for slot_idx in range(slots_per_day):
                    start_time = current_time + (slot_idx * slot_duration_minutes)
                    end_time = start_time + slot_duration_minutes
                    
                    # Convert minutes to HH:MM format
                    start_hm = f"{start_time // 60:02d}:{start_time % 60:02d}"
                    end_hm = f"{end_time // 60:02d}:{end_time % 60:02d}"
                    
                    timeslot = {
                        "id": str(slot_id),
                        "day": day_name,
                        "day_of_week": day_idx,
                        "week": week,
                        "start_time": start_hm,
                        "end_time": end_hm,
                        "slot_index": slot_idx  # Position within day
                    }
                    timeslots.append(timeslot)
                    slot_id += 1
        
        self.timeslots = timeslots
        logger.info(f"Generated {len(timeslots)} time slots")
        return timeslots
    
    def extract_courses(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Convert ITC courses to standardized format.
        
        ITC format: <course id="1">
                      <config id="1">
                        <subpart id="1"> ... </subpart>
                        <subpart id="2"> ... </subpart>
                      </config>
                    </course>
        
        Each config is like a "class group" or "section"
        Each subpart is an individual lecture
        """
        courses = []
        courses_elem = root.find('courses')
        
        if courses_elem is None:
            logger.warning("No courses found in XML")
            return courses
        
        for course_elem in courses_elem:
            course_id = course_elem.attrib.get('id')
            
            # In ITC, each course has configs (sections)
            for config_idx, config in enumerate(course_elem.findall('config')):
                config_id = config.attrib.get('id')
                
                # Extract subparts (individual lectures)
                lectures = []
                for subpart_idx, subpart in enumerate(config.findall('subpart')):
                    subpart_id = subpart.attrib.get('id')
                    
                    # Extract classes (specific lecture sessions)
                    classes = []
                    for class_elem in subpart.findall('class'):
                        class_id = class_elem.attrib.get('id')
                        class_limit = int(class_elem.attrib.get('limit', 50))
                        
                        classes.append({
                            "class_id": class_id,
                            "class_limit": class_limit,
                            "instructors": []  # Not in ITC format
                        })
                    
                    if classes:
                        lectures.append({
                            "subpart_id": subpart_id,
                            "classes": classes
                        })
                
                # Create course entry
                total_classes = sum(len(lec.get('classes', [])) for lec in lectures)
                total_limit = sum(cls.get('class_limit', 0) 
                                 for lec in lectures 
                                 for cls in lec.get('classes', []))
                
                course = {
                    "id": f"C{course_id}_{config_id}",  # Unique per config
                    "name": f"Course-{course_id}-Sec{config_id}",
                    "code": f"C{course_id}",
                    "year": "1",  # Not in ITC
                    "class_size": total_limit if total_limit > 0 else 50,
                    "hours_per_week": len(lectures),  # Approximate
                    "study_mode": "Lecture",
                    "department": "General",  # Not in ITC
                    "config_id": config_id,
                    "lectures": lectures,
                    "total_classes": total_classes
                }
                courses.append(course)
                self.courses_map[course['id']] = course
        
        logger.info(f"Extracted {len(courses)} course configurations")
        return courses
    
    def extract_students(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Convert ITC students to standardized format.
        
        ITC format: <student id="1">
                      <course id="X"/>
                      <course id="Y"/>
                    </student>
        """
        students = []
        students_elem = root.find('students')
        
        if students_elem is None:
            logger.warning("No students found in XML")
            return students
        
        for student_elem in students_elem:
            student_id = student_elem.attrib.get('id')
            
            # Get enrolled courses
            enrolled_courses = []
            for course_elem in student_elem.findall('course'):
                course_id = course_elem.attrib.get('id')
                enrolled_courses.append(course_id)
            
            student = {
                "id": f"S{student_id}",
                "name": f"Student-{student_id}",
                "email": f"student{student_id}@university.edu",
                "enrolled_courses": enrolled_courses
            }
            students.append(student)
            self.students_map[student_id] = student
        
        logger.info(f"Extracted {len(students)} students")
        return students
    
    def extract_constraints(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Convert ITC distributions to constraints.
        
        ITC distributions represent soft/hard constraints:
        - SameTime, SameRoom, SameDays: keep classes together
        - NotOverlap: prevent overlap
        - MaxDayLoad: max hours per day
        - MinGap: minimum gap between classes
        - WorkDay: preferred working days
        - etc.
        """
        constraints = []
        constraints_elem = root.find('distributions')
        
        if constraints_elem is None:
            logger.warning("No constraints found in XML")
            return constraints
        
        constraint_id = 1
        for dist in constraints_elem:
            dist_type = dist.attrib.get('type', 'Unknown')
            required = dist.attrib.get('required', 'false').lower() == 'true'
            
            # Get affected classes
            affected_classes = []
            for class_elem in dist.findall('class'):
                class_id = class_elem.attrib.get('id')
                affected_classes.append(class_id)
            
            constraint = {
                "id": str(constraint_id),
                "type": dist_type,
                "required": required,  # Hard constraint if True
                "affected_classes": affected_classes,
                "weight": 1.0 if required else 0.5
            }
            constraints.append(constraint)
            constraint_id += 1
        
        logger.info(f"Extracted {len(constraints)} constraints")
        return constraints
    
    def convert_to_json(self, xml_file: str) -> Dict[str, Any]:
        """
        Main conversion method: XML → JSON.
        
        Args:
            xml_file: Path to ITC XML file
        
        Returns:
            Dictionary with standardized timetable data
        """
        logger.info(f"Converting {Path(xml_file).name}...")
        
        root = self.parse_xml(xml_file)
        
        # Extract all components
        problem_meta = self.extract_problem_meta(root)
        rooms = self.extract_rooms(root)
        timeslots = self.extract_timeslots()
        courses = self.extract_courses(root)
        students = self.extract_students(root)
        constraints = self.extract_constraints(root)
        
        # Compile into standardized JSON schema
        timetable_data = {
            "metadata": {
                "source": "ITC",
                "source_file": Path(xml_file).name,
                "converted_at": datetime.now().isoformat(),
                "problem": problem_meta
            },
            "rooms": rooms,
            "timeslots": timeslots,
            "courses": courses,
            "students": students,
            "constraints": constraints,
            "statistics": {
                "total_rooms": len(rooms),
                "total_timeslots": len(timeslots),
                "total_courses": len(courses),
                "total_students": len(students),
                "total_constraints": len(constraints),
                "avg_class_size": sum(c.get('class_size', 0) for c in courses) / len(courses) if courses else 0,
                "avg_room_capacity": sum(r.get('capacity', 0) for r in rooms) / len(rooms) if rooms else 0
            }
        }
        
        logger.info(f"✓ Conversion complete: {Path(xml_file).name}")
        return timetable_data
    
    def save_json(self, data: Dict[str, Any], output_file: str) -> None:
        """Save JSON data to file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"✓ Saved to {output_file}")
        except IOError as e:
            logger.error(f"Failed to save {output_file}: {e}")
            raise


def convert_itc_xml_batch(input_dir: str, output_dir: str, pattern: str = "*.xml") -> List[str]:
    """
    Convert all ITC XML files in a directory to JSON.
    
    Args:
        input_dir: Directory containing XML files
        output_dir: Directory to save JSON files
        pattern: File pattern to match (default: "*.xml")
    
    Returns:
        List of converted JSON file paths
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    converted_files = []
    xml_files = list(input_path.glob(pattern))
    
    logger.info(f"Found {len(xml_files)} XML files in {input_dir}")
    
    converter = ITCXMLConverter()
    
    for i, xml_file in enumerate(xml_files, 1):
        try:
            logger.info(f"[{i}/{len(xml_files)}] Processing {xml_file.name}...")
            
            # Convert
            data = converter.convert_to_json(str(xml_file))
            
            # Save
            output_file = output_path / f"{xml_file.stem}.json"
            converter.save_json(data, str(output_file))
            converted_files.append(str(output_file))
            
            # Reset maps for next file
            converter = ITCXMLConverter()
        
        except Exception as e:
            logger.error(f"Failed to convert {xml_file.name}: {e}")
            continue
    
    logger.info(f"\n✓ Converted {len(converted_files)}/{len(xml_files)} files successfully")
    return converted_files


if __name__ == "__main__":
    """
    Usage: python itc_xml_converter.py
    
    Converts all ITC XML files in Data/ITC-data/20014070/ to JSON
    Output: backend/data/itc_json_converted/
    """
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    input_dir = "../../../../../../Data/ITC-data/20014070"
    output_dir = "../converted_data/itc_json"
    
    converted = convert_itc_xml_batch(input_dir, output_dir)
    print(f"\n{'='*70}")
    print(f"SUMMARY: Converted {len(converted)} files")
    print(f"Output directory: {output_dir}")
    print(f"{'='*70}")
