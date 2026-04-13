"""
Constraint-based timetable scheduler using OR-Tools.

Handles intelligent scheduling of courses to time slots and rooms,
respecting capacity, lecturer availability, and conflict constraints.
"""

from ortools.sat.python import cp_model
from ..models import TimetableEntry, LecturerAvailability


class TimetableScheduler:
    """
    Manages automated timetable generation using constraint programming.
    
    Constraints enforced:
    - Each course scheduled exactly once
    - No room double-bookings
    - No lecturer double-bookings
    - Room capacity >= course class size
    - Respect lecturer availability
    - Respect lecturer-course assignments
    """
    
    def __init__(self, courses, lecturers, rooms, time_slots):
        self.courses = courses
        self.lecturers = lecturers
        self.rooms = rooms
        self.time_slots = time_slots
        self.model = cp_model.CpModel()
        self.variables = {}
        self.lecturer_course_map = {}
    
    def generate(self):
        """
        Generate optimal timetable.
        
        Returns:
            list: TimetableEntry objects created, or empty list if no solution found
        """
        try:
            self._create_decision_variables()
            self._add_mandatory_constraints()
            self._add_resource_constraints()
            self._add_availability_constraints()
            
            entries = self._solve_and_create_entries()
            return entries
        
        except Exception as e:
            raise ValueError(f"Scheduling failed: {str(e)}")
    
    def _create_decision_variables(self):
        """Create boolean variables for each course-time-room combination."""
        self.variables = {}
        for c_idx, course in enumerate(self.courses):
            self.variables[c_idx] = {}
            for t_idx, time_slot in enumerate(self.time_slots):
                self.variables[c_idx][t_idx] = {}
                for r_idx, room in enumerate(self.rooms):
                    var_name = f'course_{c_idx}_time_{t_idx}_room_{r_idx}'
                    self.variables[c_idx][t_idx][r_idx] = self.model.NewBoolVar(var_name)
    
    def _add_mandatory_constraints(self):
        """
        Add constraints that must always be satisfied:
        - Each course scheduled exactly once
        - No two courses in same time slot and room
        """
        # Each course must be scheduled exactly once
        for c_idx in range(len(self.courses)):
            scheduled = []
            for t_idx in range(len(self.time_slots)):
                for r_idx in range(len(self.rooms)):
                    scheduled.append(self.variables[c_idx][t_idx][r_idx])
            self.model.Add(sum(scheduled) == 1)
        
        # No room double-bookings
        for t_idx in range(len(self.time_slots)):
            for r_idx in range(len(self.rooms)):
                room_schedule = []
                for c_idx in range(len(self.courses)):
                    room_schedule.append(self.variables[c_idx][t_idx][r_idx])
                self.model.Add(sum(room_schedule) <= 1)
    
    def _add_resource_constraints(self):
        """
        Add resource-based constraints:
        - Room capacity must accommodate course size
        - Assign lecturers based on department match
        - Prevent lecturer double-bookings
        """
        # Assign lecturers by department
        for c_idx, course in enumerate(self.courses):
            # Find lecturer from same department
            lecturer = next(
                (l for l in self.lecturers if l.department == course.department),
                self.lecturers[0] if self.lecturers else None
            )
            if lecturer:
                self.lecturer_course_map[c_idx] = lecturer
        
        # Room capacity constraints
        for c_idx, course in enumerate(self.courses):
            for t_idx in range(len(self.time_slots)):
                for r_idx, room in enumerate(self.rooms):
                    # Can't assign if room too small
                    if room.capacity < course.class_size:
                        self.model.Add(self.variables[c_idx][t_idx][r_idx] == 0)
        
        # Lecturer double-booking prevention
        for l_idx, lecturer in enumerate(self.lecturers):
            courses_for_lecturer = [
                c_idx for c_idx in self.lecturer_course_map
                if self.lecturer_course_map[c_idx] == lecturer
            ]
            for t_idx in range(len(self.time_slots)):
                lecturer_schedule = []
                for c_idx in courses_for_lecturer:
                    for r_idx in range(len(self.rooms)):
                        lecturer_schedule.append(self.variables[c_idx][t_idx][r_idx])
                if lecturer_schedule:
                    self.model.Add(sum(lecturer_schedule) <= 1)
    
    def _add_availability_constraints(self):
        """
        Add lecturer availability constraints.
        If a lecturer is marked unavailable at a time slot, can't schedule then.
        """
        availabilities = list(LecturerAvailability.objects.filter(is_available=False))
        
        for avail in availabilities:
            # Find this time slot index
            t_idx = None
            for i, ts in enumerate(self.time_slots):
                if ts.id == avail.time_slot.id:
                    t_idx = i
                    break
            
            if t_idx is None:
                continue
            
            # Find courses taught by this lecturer
            for c_idx, course in enumerate(self.courses):
                if c_idx in self.lecturer_course_map:
                    if self.lecturer_course_map[c_idx].id == avail.lecturer.id:
                        # Can't schedule this course at this time
                        for r_idx in range(len(self.rooms)):
                            self.model.Add(self.variables[c_idx][t_idx][r_idx] == 0)
    
    def _solve_and_create_entries(self):
        """
        Solve the constraint model and create TimetableEntry objects.
        
        Returns:
            list: Created TimetableEntry objects
        """
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return []
        
        entries = []
        for c_idx, course in enumerate(self.courses):
            for t_idx, time_slot in enumerate(self.time_slots):
                for r_idx, room in enumerate(self.rooms):
                    if int(solver.Value(self.variables[c_idx][t_idx][r_idx])):
                        lecturer = self.lecturer_course_map.get(c_idx)
                        if lecturer:
                            entry = TimetableEntry.objects.create(
                                course=course,
                                lecturer=lecturer,
                                room=room,
                                time_slot=time_slot
                            )
                            entries.append(entry)
        
        return entries
