"""
Synthetic Timetable Data Generator

Generates realistic synthetic university timetable data for ML training.
Creates balanced, feasible timetable instances to augment ITC competition datasets.

Features:
- Configurable scale (200+ courses, 50+ lecturers, 30+ rooms)
- Realistic departmental structure
- Constraint generation
- Ensures data diversity
"""

import json
import random
from typing import Dict, List, Any
from datetime import datetime, time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SyntheticTimetableGenerator:
    """Generate realistic synthetic timetable data."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with optional seed for reproducibility."""
        random.seed(seed)
        self.seed = seed
    
    def generate_metadata(self, 
                         name: str,
                         nr_days: int = 5,
                         nr_weeks: int = 15,
                         slots_per_day: int = 48) -> Dict[str, Any]:
        """Generate problem metadata."""
        return {
            "problem_name": name,
            "nr_days": nr_days,
            "nr_weeks": nr_weeks,
            "slots_per_day": slots_per_day,
            "optimization_weights": {
                "time": 4,      # Minimize total time conflicts
                "room": 1,      # Minimize room conflicts
                "distribution": 15,  # Respect soft constraints heavily
                "student": 5    # Minimize student conflicts
            }
        }
    
    def generate_rooms(self, num_rooms: int = 30) -> List[Dict[str, Any]]:
        """
        Generate realistic room data.
        
        Room types:
        - Lecture halls (100-300 seats)
        - Medium classrooms (50-100 seats)
        - Small classrooms (25-50 seats)
        - Labs (30 seats)
        """
        rooms = []
        departments = ["Main Building", "Science Block", "Engineering Block", "Arts Building"]
        room_types = [
            ("Lecture Hall", 100, 300),
            ("Large Classroom", 60, 100),
            ("Medium Classroom", 40, 60),
            ("Small Classroom", 20, 40),
            ("Lab", 20, 35)
        ]
        
        room_id = 1
        for _ in range(num_rooms):
            room_type, min_cap, max_cap = random.choice(room_types)
            capacity = random.randint(min_cap, max_cap)
            
            room = {
                "id": str(room_id),
                "name": f"{room_type}-{room_id}",
                "capacity": capacity,
                "building": random.choice(departments),
                "room_type": room_type,
                "travel_times": {}  # Can be populated if needed
            }
            rooms.append(room)
            room_id += 1
        
        logger.info(f"Generated {len(rooms)} rooms")
        return rooms
    
    def generate_timeslots(self, 
                          nr_days: int = 5,
                          nr_weeks: int = 15,
                          slots_per_day: int = 48) -> List[Dict[str, Any]]:
        """
        Generate time slots.
        
        Typical schedule: 8:00 AM - 6:00 PM (each slot = 30 min)
        Days: Monday - Friday
        """
        timeslots = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][:nr_days]
        
        slot_duration_min = 30
        start_hour = 8
        end_hour = 18
        
        slot_id = 1
        for week in range(1, nr_weeks + 1):
            for day_idx, day_name in enumerate(days):
                hour = start_hour
                for slot_idx in range(slots_per_day):
                    minute = (slot_idx * slot_duration_min) % 60
                    if (slot_idx * slot_duration_min) >= 600:  # After 10 hours
                        break
                    
                    start_min = start_hour * 60 + slot_idx * slot_duration_min
                    end_min = start_min + slot_duration_min
                    
                    start_hm = f"{start_min // 60:02d}:{start_min % 60:02d}"
                    end_hm = f"{end_min // 60:02d}:{end_min % 60:02d}"
                    
                    timeslot = {
                        "id": str(slot_id),
                        "day": day_name,
                        "day_of_week": day_idx,
                        "week": week,
                        "start_time": start_hm,
                        "end_time": end_hm,
                        "slot_index": slot_idx
                    }
                    timeslots.append(timeslot)
                    slot_id += 1
        
        logger.info(f"Generated {len(timeslots)} time slots")
        return timeslots
    
    def generate_lecturers(self, num_lecturers: int = 50) -> List[Dict[str, Any]]:
        """Generate realistic lecturer data."""
        lecturers = []
        departments = ["Computer Science", "Mathematics", "Physics", "Chemistry", 
                      "Biology", "Engineering", "Literature", "Economics"]
        
        for i in range(1, num_lecturers + 1):
            lecturer = {
                "id": f"L{i}",
                "name": f"Dr. Lecturer-{i}",
                "employee_id": f"EMP{i:05d}",
                "department": random.choice(departments),
                "courses": [],  # Will assign later
                "availability": self._generate_availability()
            }
            lecturers.append(lecturer)
        
        logger.info(f"Generated {len(lecturers)} lecturers")
        return lecturers
    
    def _generate_availability(self) -> List[str]:
        """Generate lecturer availability (which timeslots they can teach)."""
        # Most lecturers available all slots, some have restrictions
        if random.random() < 0.3:  # 30% have availability constraints
            # Prefer morning/afternoon only
            availability = []
            for hour in range(8, 18):
                if random.random() < 0.8:  # 80% availability
                    availability.append(f"{hour:02d}:00")
            return availability
        return []  # Empty means available all times
    
    def generate_courses(self, 
                        lecturers: List[Dict[str, Any]],
                        rooms: List[Dict[str, Any]],
                        num_courses: int = 200) -> List[Dict[str, Any]]:
        """
        Generate realistic course data.
        
        Distribution:
        - Year 1-3 courses
        - Various class sizes
        - Multiple sections for popular courses
        """
        courses = []
        departments = ["Computer Science", "Mathematics", "Physics", "Chemistry", 
                      "Biology", "Engineering", "Literature", "Economics"]
        
        course_id = 1
        for _ in range(num_courses):
            dept = random.choice(departments)
            year = random.randint(1, 3)
            
            course_code = f"{dept[:3].upper()}{random.randint(100, 499)}"
            class_size = random.choice([30, 40, 50, 60, 80, 100, 120, 150])
            
            # Find suitable room (capacity >= class_size)
            suitable_rooms = [r for r in rooms if r['capacity'] >= class_size]
            selected_room = random.choice(suitable_rooms) if suitable_rooms else random.choice(rooms)
            
            # Assign lecturers (1-3 per course)
            num_lecturers_per_course = random.randint(1, 3)
            course_lecturers = random.sample(lecturers, min(num_lecturers_per_course, len(lecturers)))
            lecturer_ids = [l['id'] for l in course_lecturers]
            
            # Generate lectures (weekly meetings)
            meetings_per_week = random.randint(2, 4)
            
            course = {
                "id": f"C{course_id}",
                "name": f"{course_code}-{random.randint(1, 3)}",  # Sections
                "code": course_code,
                "year": str(year),
                "class_size": class_size,
                "hours_per_week": meetings_per_week,
                "study_mode": random.choice(["Lecture", "Lab", "Seminar"]),
                "department": dept,
                "preferred_room": selected_room['id'],
                "lecturer_ids": lecturer_ids,
                "lectures": [{"lecture_id": f"L{j}", "duration": 1} for j in range(meetings_per_week)]
            }
            courses.append(course)
            
            # Update lecturer course assignments
            for lec_id in lecturer_ids:
                for lec in lecturers:
                    if lec['id'] == lec_id:
                        lec['courses'].append(course['id'])
            
            course_id += 1
        
        logger.info(f"Generated {len(courses)} courses")
        return courses
    
    def generate_students(self, 
                         courses: List[Dict[str, Any]],
                         num_students: int = 1000) -> List[Dict[str, Any]]:
        """Generate realistic student data with course enrollments."""
        students = []
        
        for i in range(1, num_students + 1):
            # Each student takes 4-6 courses
            num_courses_per_student = random.randint(4, 6)
            enrolled_courses = random.sample([c['id'] for c in courses], 
                                             min(num_courses_per_student, len(courses)))
            
            student = {
                "id": f"S{i}",
                "name": f"Student-{i}",
                "email": f"student{i}@university.edu",
                "enrolled_courses": enrolled_courses
            }
            students.append(student)
        
        logger.info(f"Generated {len(students)} students")
        return students
    
    def generate_constraints(self, 
                            courses: List[Dict[str, Any]],
                            num_constraints: int = None) -> List[Dict[str, Any]]:
        """
        Generate realistic constraints.
        
        Constraint types:
        - SameTime: sections of same course should have same schedule
        - NotOverlap: prevent lecturer/student overlaps
        - MinGap: minimum gap between lectures
        - MaxDayLoad: max hours per day per student
        """
        constraints = []
        
        if num_constraints is None:
            num_constraints = len(courses) // 2  # ~50% of courses have constraints
        
        constraint_types = [
            ("SameTime", True),        # Hard constraint
            ("SameDays", False),       # Soft constraint
            ("MinGap(30)", False),     # Min 30-min gap between classes
            ("MaxDayLoad(6)", False),  # Max 6 hours per day
            ("NotOverlap", True)       # Hard constraint
        ]
        
        constraint_id = 1
        for _ in range(min(num_constraints, len(courses))):
            constraint_type, required = random.choice(constraint_types)
            
            # Pick affected courses
            num_affected = random.randint(2, 4)
            affected = random.sample([c['id'] for c in courses], 
                                    min(num_affected, len(courses)))
            
            constraint = {
                "id": str(constraint_id),
                "type": constraint_type,
                "required": required,
                "affected_courses": affected,
                "weight": 1.0 if required else random.uniform(0.3, 0.9)
            }
            constraints.append(constraint)
            constraint_id += 1
        
        logger.info(f"Generated {len(constraints)} constraints")
        return constraints
    
    def generate_timetable(self,
                          name: str = "synthetic_timetable",
                          num_courses: int = 200,
                          num_lecturers: int = 50,
                          num_rooms: int = 30,
                          num_students: int = 1000) -> Dict[str, Any]:
        """
        Main method: Generate complete synthetic timetable.
        
        Args:
            name: Name for the problem instance
            num_courses: Number of courses to generate
            num_lecturers: Number of lecturers
            num_rooms: Number of rooms
            num_students: Number of students
        
        Returns:
            Complete timetable data in standardized JSON format
        """
        logger.info(f"Generating synthetic timetable: {name}")
        logger.info(f"  Courses: {num_courses}, Lecturers: {num_lecturers}, Rooms: {num_rooms}, Students: {num_students}")
        
        # Generate components
        metadata = self.generate_metadata(name)
        rooms = self.generate_rooms(num_rooms)
        timeslots = self.generate_timeslots(metadata['nr_days'], 
                                           metadata['nr_weeks'], 
                                           metadata['slots_per_day'])
        lecturers = self.generate_lecturers(num_lecturers)
        courses = self.generate_courses(lecturers, rooms, num_courses)
        students = self.generate_students(courses, num_students)
        constraints = self.generate_constraints(courses)
        
        # Compile
        timetable_data = {
            "metadata": {
                "source": "Synthetic",
                "generator": "SyntheticTimetableGenerator",
                "generated_at": datetime.now().isoformat(),
                "seed": self.seed,
                "problem": metadata
            },
            "rooms": rooms,
            "timeslots": timeslots,
            "lecturers": lecturers,
            "courses": courses,
            "students": students,
            "constraints": constraints,
            "statistics": {
                "total_rooms": len(rooms),
                "total_timeslots": len(timeslots),
                "total_lecturers": len(lecturers),
                "total_courses": len(courses),
                "total_students": len(students),
                "total_constraints": len(constraints),
                "avg_class_size": sum(c.get('class_size', 0) for c in courses) / len(courses) if courses else 0,
                "avg_room_capacity": sum(r.get('capacity', 0) for r in rooms) / len(rooms) if rooms else 0,
                "lecturer_course_ratio": len(courses) / len(lecturers),
                "student_course_ratio": sum(len(s.get('enrolled_courses', [])) for s in students) / len(students) if students else 0
            }
        }
        
        logger.info("✓ Synthetic timetable generation complete")
        return timetable_data
    
    def save_json(self, data: Dict[str, Any], output_file: str) -> None:
        """Save JSON data to file."""
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"✓ Saved to {output_file}")
        except IOError as e:
            logger.error(f"Failed to save {output_file}: {e}")
            raise


def generate_synthetic_batch(output_dir: str, 
                            num_instances: int = 10,
                            variations: List[Dict[str, int]] = None) -> List[str]:
    """
    Generate multiple synthetic timetable instances with variations.
    
    Args:
        output_dir: Directory to save JSON files
        num_instances: Number of instances to generate
        variations: List of size configurations (if None, uses defaults)
    
    Returns:
        List of generated file paths
    """
    if variations is None:
        variations = [
            {"courses": 50, "lecturers": 15, "rooms": 10, "students": 200},      # Small
            {"courses": 100, "lecturers": 30, "rooms": 20, "students": 500},     # Medium
            {"courses": 200, "lecturers": 50, "rooms": 30, "students": 1000},    # Large
        ]
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for i in range(num_instances):
        variation = variations[i % len(variations)]
        generator = SyntheticTimetableGenerator(seed=42 + i)
        
        logger.info(f"\n[{i+1}/{num_instances}] Generating instance {i+1}...")
        
        data = generator.generate_timetable(
            name=f"synthetic_{i+1}",
            num_courses=variation['courses'],
            num_lecturers=variation['lecturers'],
            num_rooms=variation['rooms'],
            num_students=variation['students']
        )
        
        output_file = output_path / f"synthetic_{i+1}.json"
        generator.save_json(data, str(output_file))
        generated_files.append(str(output_file))
    
    logger.info(f"\n✓ Generated {len(generated_files)} synthetic instances")
    return generated_files


if __name__ == "__main__":
    """
    Usage: python synthetic_data_generator.py
    
    Generates synthetic timetable data for ML training.
    Output: backend/data/synthetic_json/
    """
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    output_dir = "../converted_data/synthetic"
    
    # Generate 10 synthetic instances (mix of small, medium, large)
    variations = [
        {"courses": 50, "lecturers": 15, "rooms": 10, "students": 200},      # Small
        {"courses": 100, "lecturers": 30, "rooms": 20, "students": 500},     # Medium
        {"courses": 200, "lecturers": 50, "rooms": 30, "students": 1000},    # Large
    ]
    
    generated = generate_synthetic_batch(output_dir, num_instances=15, variations=variations)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY: Generated {len(generated)} synthetic instances")
    print(f"Output directory: {output_dir}")
    print(f"{'='*70}")
