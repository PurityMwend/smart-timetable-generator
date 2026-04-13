"""
Data models for the Smart Timetable Generator.

Entities:
  - User          Custom auth model with Admin / Viewer roles
  - Department    Organisational unit (e.g. "Computer Science")
  - Course        A lecture/unit to be scheduled
  - Lecturer      Teaching staff member
  - Room          Physical venue for lectures
  - TimeSlot      Available time window (day + start/end time)
  - TimetableEntry  A single scheduled lecture (the output)
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


# ---------------------------------------------------------------------------
# Custom User
# ---------------------------------------------------------------------------

class User(AbstractUser):
    """
    Custom user with role-based access:
    - TIMETABLER: Superuser privileges, can manage all aspects
    - LECTURER: Can view timetables, manage own schedule (no editing timetables)
    - STUDENT: Read-only access
    
    Roles are assigned automatically based on email domain:
    - @admin.cuk.ac.ke → TIMETABLER (superuser)
    - @staff.cuk.ac.ke → LECTURER (limited privileges)
    - @student.cuk.ac.ke → STUDENT (read-only)
    """

    class Role(models.TextChoices):
        TIMETABLER = 'TIMETABLER', 'Timetabler (Admin)'
        LECTURER = 'LECTURER', 'Lecturer'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(
        max_length=15,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text='Determines access level based on email domain.',
    )

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_timetabler(self):
        """Check if user is a timetabler (superuser)."""
        return self.role == self.Role.TIMETABLER

    @property
    def is_lecturer(self):
        """Check if user is a lecturer."""
        return self.role == self.Role.LECTURER

    @property
    def is_student(self):
        """Check if user is a student."""
        return self.role == self.Role.STUDENT

    @property
    def is_admin_user(self):
        """Backward compatibility: admin users are timetablers with superuser."""
        return self.is_timetabler and self.is_superuser


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

class School(models.Model):
    """Academic school or faculty containing multiple departments."""

    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text='Short code, e.g. "CMP", "BUS".',
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.code} – {self.name}'


class Department(models.Model):
    """Academic department or faculty."""

    school = models.ForeignKey(
        'School',
        on_delete=models.CASCADE,
        related_name='departments',
        null=True,
        blank=True,
        help_text='School this department belongs to.'
    )
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text='Short code, e.g. "CS", "ENG".',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.code} – {self.name}'


class Course(models.Model):
    """A lecture/unit that needs to be scheduled."""

    class StudyMode(models.TextChoices):
        IN_PERSON = 'IN_PERSON', 'In-Person'
        HYBRID = 'HYBRID', 'Hybrid'
        ONLINE = 'ONLINE', 'Online'

    name = models.CharField(max_length=200)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Course code, e.g. "CS101".',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses',
    )
    year_of_study = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Academic year (1, 2, 3, …).',
    )
    study_mode = models.CharField(
        max_length=15,
        choices=StudyMode.choices,
        default=StudyMode.IN_PERSON,
    )
    class_size = models.PositiveIntegerField(
        help_text='Expected number of students.',
    )
    hours_per_week = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=3.0,
        help_text='Number of lecture hours per week.',
    )

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} – {self.name}'


class Lecturer(models.Model):
    """Teaching staff member."""

    name = models.CharField(max_length=200)
    employee_id = models.CharField(
        max_length=30,
        unique=True,
        help_text='Staff/employee number.',
    )
    email = models.EmailField(blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='lecturers',
    )
    courses = models.ManyToManyField(
        Course,
        related_name='lecturers',
        blank=True,
        help_text='Courses this lecturer can teach.',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.employee_id})'


class Room(models.Model):
    """Physical venue for lectures."""

    class RoomType(models.TextChoices):
        LECTURE_HALL = 'LECTURE_HALL', 'Lecture Hall'
        CLASSROOM = 'CLASSROOM', 'Classroom'
        SEMINAR = 'SEMINAR', 'Seminar Room'

    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(
        help_text='Maximum number of students the room can hold.',
    )
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.CLASSROOM,
    )

    class Meta:
        ordering = ['building', 'name']
        unique_together = ['building', 'name']

    def __str__(self):
        if self.building:
            return f'{self.building} – {self.name} (cap. {self.capacity})'
        return f'{self.name} (cap. {self.capacity})'


class TimeSlot(models.Model):
    """A defined time window in the weekly schedule."""

    class Day(models.TextChoices):
        MONDAY = 'MON', 'Monday'
        TUESDAY = 'TUE', 'Tuesday'
        WEDNESDAY = 'WED', 'Wednesday'
        THURSDAY = 'THU', 'Thursday'
        FRIDAY = 'FRI', 'Friday'

    day = models.CharField(max_length=3, choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day', 'start_time']
        unique_together = ['day', 'start_time', 'end_time']

    def __str__(self):
        return f'{self.get_day_display()} {self.start_time:%H:%M}–{self.end_time:%H:%M}'


class LecturerAvailability(models.Model):
    """Marks a time-slot as available or unavailable for a lecturer."""

    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.CASCADE,
        related_name='availabilities',
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='lecturer_availabilities',
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['lecturer', 'time_slot']
        verbose_name_plural = 'Lecturer availabilities'

    def __str__(self):
        status = 'Available' if self.is_available else 'Unavailable'
        return f'{self.lecturer.name} – {self.time_slot} ({status})'


# ---------------------------------------------------------------------------
# Timetable output
# ---------------------------------------------------------------------------

class TimetableEntry(models.Model):
    """A single scheduled lecture – the core output of the generator."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='timetable_entries',
    )
    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.CASCADE,
        related_name='timetable_entries',
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='timetable_entries',
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='timetable_entries',
    )
    is_locked = models.BooleanField(
        default=False,
        help_text='If True, the scheduler will not move this entry.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['time_slot__day', 'time_slot__start_time']
        verbose_name_plural = 'Timetable entries'
        constraints = [
            # A room can only host one lecture per time-slot.
            models.UniqueConstraint(
                fields=['room', 'time_slot'],
                name='unique_room_per_timeslot',
            ),
            # A lecturer can only teach one lecture per time-slot.
            models.UniqueConstraint(
                fields=['lecturer', 'time_slot'],
                name='unique_lecturer_per_timeslot',
            ),
        ]

    def __str__(self):
        return (
            f'{self.course.code} | {self.lecturer.name} | '
            f'{self.room.name} | {self.time_slot}'
        )

# ---------------------------------------------------------------------------
# Training Data Models
# ---------------------------------------------------------------------------

class CommonUnit(models.Model):
    """
    A unit/course taught across multiple departments.
    E.g. "Information Systems Security and Audit" might be taught in CS, ENG, etc.
    """
    
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    hours_per_week = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=3.0,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} – {self.name}'


class RecurrentUnit(models.Model):
    """
    A unit that recurs in specific courses and years.
    E.g. Software Engineering 4.2 has "Information Systems Security and Audit"
    """
    
    unit = models.ForeignKey(
        CommonUnit,
        on_delete=models.CASCADE,
        related_name='recurrent_in',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='recurrent_units',
    )
    year_of_study = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Year in which this unit is taught (1, 2, 3, 4, etc.)',
    )
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), ],
        help_text='Semester (1 or 2)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course', 'year_of_study', 'semester']
        unique_together = ['unit', 'course', 'year_of_study', 'semester']
        verbose_name_plural = 'Recurrent units'

    def __str__(self):
        return f'{self.course.code} {self.year_of_study}.{self.semester} – {self.unit.code}'


class TrainingData(models.Model):
    """
    Aggregated training data for ML model training.
    Includes courses, lecturers, departments, common units, and recurrent patterns.
    Admin only - used to train scheduling algorithms.
    """
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Data inclusions
    courses = models.ManyToManyField(
        Course,
        related_name='training_data_sets',
        blank=True,
        help_text='Courses included in this training dataset',
    )
    lecturers = models.ManyToManyField(
        Lecturer,
        related_name='training_data_sets',
        blank=True,
        help_text='Lecturers included in this training dataset',
    )
    departments = models.ManyToManyField(
        Department,
        related_name='training_data_sets',
        blank=True,
        help_text='Departments included in this training dataset',
    )
    common_units = models.ManyToManyField(
        CommonUnit,
        related_name='training_data_sets',
        blank=True,
        help_text='Common units included in this training dataset',
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_training_datasets',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Model info
    trained_model_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Path to trained ML model file (if trained)',
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Whether this dataset is actively used for training',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Training data sets'

    def __str__(self):
        return f'{self.name} (created {self.created_at.strftime("%Y-%m-%d")})'