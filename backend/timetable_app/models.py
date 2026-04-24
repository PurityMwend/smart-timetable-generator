from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(AbstractUser):
    """Custom User model with roles for the timetable system."""
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('viewer', 'Viewer'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    school = models.ForeignKey('School', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class School(models.Model):
    """Represents a school or institution."""
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schools'
        ordering = ['name']
        verbose_name_plural = 'Schools'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(models.Model):
    """Represents a department within a school."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    head_of_department = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        unique_together = ('school', 'code')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.school.code}"


class Program(models.Model):
    """Represents a degree program or course program."""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    level = models.CharField(
        max_length=20,
        choices=[
            ('100', 'First Year'),
            ('200', 'Second Year'),
            ('300', 'Third Year'),
            ('400', 'Fourth Year'),
        ]
    )
    duration_semesters = models.IntegerField(default=2, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'programs'
        unique_together = ('department', 'code')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.code} ({self.get_level_display()})"


class Course(models.Model):
    """Represents a course/subject (e.g. BIT Year 1, CS Year 2)."""
    # program is now optional, as courses can belong directly to departments
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    # Direct department link for hierarchy drill-down (School→Dept→Course)
    department = models.ForeignKey(
        'Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='direct_courses'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    credits = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(10)])
    semester = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(8)])
    description = models.TextField(blank=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependent_courses')
    is_core = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        unique_together = ('department', 'code')
        ordering = ['semester', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Lecturer(models.Model):
    """Represents a lecturer/instructor."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='lecturers')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='lecturers')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100, blank=True)  # Prof, Dr, Mr, etc.
    max_hours_per_week = models.IntegerField(default=20, validators=[MinValueValidator(1)])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lecturers'
        unique_together = ('school', 'employee_id')
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Room(models.Model):
    """Represents a classroom/lecture hall."""
    ROOM_TYPE_CHOICES = (
        ('lecture', 'Lecture Hall'),
        ('lab', 'Laboratory'),
        ('seminar', 'Seminar Room'),
        ('studio', 'Studio'),
        ('workshop', 'Workshop'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='rooms')
    building = models.CharField(max_length=100)
    room_number = models.CharField(max_length=50)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='lecture')
    capacity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    has_projector = models.BooleanField(default=True)
    has_computer = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rooms'
        unique_together = ('school', 'building', 'room_number')
        ordering = ['building', 'room_number']
    
    def __str__(self):
        return f"{self.building} - {self.room_number} ({self.get_room_type_display()})"


class CourseAllocation(models.Model):
    """Maps lecturers to courses they teach."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='allocations')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='course_allocations')
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    academic_year = models.CharField(max_length=9)  # e.g., "2024/2025"
    hours_per_week = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_allocations'
        unique_together = ('course', 'lecturer', 'semester', 'academic_year')
    
    def __str__(self):
        return f"{self.lecturer.full_name} - {self.course.code}"


class StudentClass(models.Model):
    """Represents a class of students taking a course."""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='classes')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    class_name = models.CharField(max_length=100)  # e.g., "CS 200 A", "ENG 201 B"
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    academic_year = models.CharField(max_length=9)  # e.g., "2024/2025"
    student_count = models.IntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_classes'
        unique_together = ('course', 'class_name', 'semester', 'academic_year')
    
    def __str__(self):
        return f"{self.class_name} - {self.course.code}"


class TimeSlot(models.Model):
    """Represents available time slots for scheduling."""
    DAY_CHOICES = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='time_slots')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_name = models.CharField(max_length=100, blank=True)  # e.g., "Morning 1", "Afternoon 2"
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'time_slots'
        unique_together = ('school', 'day', 'start_time', 'end_time')
        ordering = ['day', 'start_time']
    
    def __str__(self):
        return f"{self.get_day_display()} {self.start_time}-{self.end_time}"


class LecturerAvailability(models.Model):
    """Tracks when lecturers are available/unavailable."""
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='availabilities')
    day = models.CharField(
        max_length=3,
        choices=[
            ('MON', 'Monday'),
            ('TUE', 'Tuesday'),
            ('WED', 'Wednesday'),
            ('THU', 'Thursday'),
            ('FRI', 'Friday'),
            ('SAT', 'Saturday'),
        ]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=255, blank=True)  # e.g., "Teaching at another campus"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lecturer_availability'
        ordering = ['day', 'start_time']
    
    def __str__(self):
        return f"{self.lecturer.full_name} - {self.get_day_display()}"


class Timetable(models.Model):
    """Represents a generated timetable."""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='timetables')
    name = models.CharField(max_length=255)
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    academic_year = models.CharField(max_length=9)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_timetables')
    generated_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timetables'
        unique_together = ('program', 'semester', 'academic_year')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.program.code} - {self.academic_year} Semester {self.semester}"


class TimetableEntry(models.Model):
    """Individual entry in a timetable (a scheduled session)."""
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='entries')
    student_class = models.ForeignKey(StudentClass, on_delete=models.CASCADE, related_name='timetable_entries')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timetable_entries')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='timetable_entries')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='timetable_entries')
    
    day = models.CharField(
        max_length=3,
        choices=[
            ('MON', 'Monday'),
            ('TUE', 'Tuesday'),
            ('WED', 'Wednesday'),
            ('THU', 'Thursday'),
            ('FRI', 'Friday'),
            ('SAT', 'Saturday'),
        ]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.FloatField(validators=[MinValueValidator(0.5), MaxValueValidator(4)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timetable_entries'
        ordering = ['day', 'start_time']
    
    def __str__(self):
        return f"{self.course.code} - {self.get_day_display()} {self.start_time}"


class TrainingData(models.Model):
    """Stores training data files for ML models."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='training_data')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
        ]
    )
    data_type = models.CharField(
        max_length=50,
        choices=[
            ('courses', 'Courses'),
            ('lecturers', 'Lecturers'),
            ('rooms', 'Rooms'),
            ('timetable', 'Timetable'),
            ('constraints', 'Constraints'),
        ]
    )
    file_size = models.IntegerField()  # in bytes
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_training_data')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processing_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'training_data'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.file_name} ({self.data_type})"


class CommonUnit(models.Model):
    """Represents a course that's common across multiple programs."""
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='common_units')
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    programs = models.ManyToManyField(Program, related_name='common_units')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'common_units'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Unit(models.Model):
    """
    A schedulable unit (e.g. BCIT 1202 — Data Communication).
    Units are global and can be shared across many courses / departments / schools.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    credits = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    hours_per_week = models.IntegerField(default=3, validators=[MinValueValidator(1)])
    # Many-to-many: a unit can appear in many courses
    courses = models.ManyToManyField(
        'Course',
        related_name='units',
        blank=True,
        through='CourseUnit',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'units'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class CourseUnit(models.Model):
    """Through table for Unit ↔ Course many-to-many."""
    unit   = models.ForeignKey(Unit,   on_delete=models.CASCADE, related_name='course_links')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='unit_links')
    year_of_study = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(6)])
    semester      = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(2)])
    is_core       = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_units'
        unique_together = ('unit', 'course')
        ordering = ['year_of_study', 'semester', 'unit__code']

    def __str__(self):
        return f"{self.unit.code} in {self.course.code}"


class RecurrentUnit(models.Model):
    """Represents courses that repeat/persist across academic years."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='recurrences')
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    expected_enrollment = models.IntegerField(validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recurrent_units'
        unique_together = ('course', 'academic_year', 'semester')
    
    def __str__(self):
        return f"{self.course.code} - {self.academic_year}"
