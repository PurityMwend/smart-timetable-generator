"""
DRF serializers for all timetable models.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    User,
    School,
    Department,
    Course,
    Lecturer,
    Room,
    TimeSlot,
    LecturerAvailability,
    TimetableEntry,
    CommonUnit,
    RecurrentUnit,
    TrainingData,
)
from .validators import (
    validate_time_slot,
    validate_timetable_entry_constraints,
    validate_cuk_email,
    validate_email_not_registered,
    get_user_role_from_email,
)



# ============================================================================
# User Authentication Serializers
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model without exposing password."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_timetabler = serializers.SerializerMethodField()
    is_lecturer = serializers.SerializerMethodField()
    is_student = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'role_display', 'is_active', 'date_joined',
            'is_timetabler', 'is_lecturer', 'is_student'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_is_timetabler(self, obj):
        return obj.is_timetabler
    
    def get_is_lecturer(self, obj):
        return obj.is_lecturer
    
    def get_is_student(self, obj):
        return obj.is_student


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Email domain determines the role automatically.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name'
        ]
    
    def validate_email(self, value):
        """Validate email is from allowed CUK domain."""
        try:
            validate_cuk_email(value)
            validate_email_not_registered(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate_username(self, value):
        """Validate username is not already taken."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate(self, data):
        """Validate password confirmation matches."""
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError(
                {'password': 'Passwords do not match.'}
            )
        return data
    
    def create(self, validated_data):
        """Create user with role determined by email domain."""
        email = validated_data['email']
        role = get_user_role_from_email(email)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=email,
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=role,
            is_active=True
        )
        
        # Set timetablers as superusers
        if role == User.Role.TIMETABLER:
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Authenticate user."""
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError(
                "Username and password are required."
            )
        
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError(
                "Invalid credentials."
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                "User account is inactive."
            )
        
        data['user'] = user
        return data


# ============================================================================
# Domain Model Serializers
# ============================================================================

class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    courses_count = serializers.SerializerMethodField()
    lecturers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'school', 'courses_count', 'lecturers_count']
    
    def get_courses_count(self, obj):
        return obj.courses.count()
    
    def get_lecturers_count(self, obj):
        return obj.lecturers.count()


class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model with nested Departments."""
    departments = DepartmentSerializer(many=True, read_only=True)
    departments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = ['id', 'name', 'code', 'description', 'departments_count', 'departments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_departments_count(self, obj):
        return obj.departments.count()


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model with nested Department."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    lecturers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'name', 'department', 'department_name', 'department_code',
            'year_of_study', 'study_mode', 'class_size', 'hours_per_week', 'lecturers_count'
        ]
    
    def get_lecturers_count(self, obj):
        return obj.lecturers.count()


class LecturerSerializer(serializers.ModelSerializer):
    """Serializer for Lecturer model."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    courses_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Lecturer
        fields = [
            'id', 'name', 'employee_id', 'email', 'department',
            'department_name', 'courses', 'courses_list'
        ]
    
    def get_courses_list(self, obj):
        """Return list of course codes."""
        return [course.code for course in obj.courses.all()]


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model."""
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'building', 'capacity', 'room_type', 'room_type_display']


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot model."""
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']
    
    def validate(self, data):
        """Validate that start_time is before end_time."""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                "Start time must be before end time."
            )
        
        return data


class LecturerAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for LecturerAvailability model."""
    lecturer_name = serializers.CharField(source='lecturer.name', read_only=True)
    time_slot_display = serializers.StringRelatedField(source='time_slot', read_only=True)
    
    class Meta:
        model = LecturerAvailability
        fields = ['id', 'lecturer', 'lecturer_name', 'time_slot', 'time_slot_display', 'is_available']


class TimetableEntrySerializer(serializers.ModelSerializer):
    """Serializer for TimetableEntry model with nested relationships."""
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_class_size = serializers.IntegerField(source='course.class_size', read_only=True)
    lecturer_name = serializers.CharField(source='lecturer.name', read_only=True)
    lecturer_email = serializers.EmailField(source='lecturer.email', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_building = serializers.CharField(source='room.building', read_only=True)
    room_capacity = serializers.IntegerField(source='room.capacity', read_only=True)
    time_slot_display = serializers.StringRelatedField(source='time_slot', read_only=True)
    day_display = serializers.CharField(source='time_slot.get_day_display', read_only=True)
    start_time = serializers.TimeField(source='time_slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='time_slot.end_time', read_only=True)

    class Meta:
        model = TimetableEntry
        fields = [
            'id', 'course', 'course_code', 'course_name', 'course_class_size',
            'lecturer', 'lecturer_name', 'lecturer_email',
            'room', 'room_name', 'room_building', 'room_capacity',
            'time_slot', 'time_slot_display', 'day_display', 'start_time', 'end_time',
            'is_locked', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate all timetable entry constraints:
        - Room capacity >= course class size
        - Lecturer is assigned to the course
        - Lecturer is available at the time slot
        - No room double-booking
        - No lecturer double-booking
        """
        course = data.get('course')
        lecturer = data.get('lecturer')
        room = data.get('room')
        time_slot = data.get('time_slot')
        
        if course and lecturer and room and time_slot:
            # Check if this is an update operation
            exclude_id = None
            if self.instance:
                exclude_id = self.instance.id
            
            try:
                validate_timetable_entry_constraints(
                    course, lecturer, room, time_slot, exclude_id
                )
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        
        return data

# ============================================================================
# Training Data Serializers
# ============================================================================

class CommonUnitSerializer(serializers.ModelSerializer):
    """Serializer for CommonUnit model."""
    
    class Meta:
        model = CommonUnit
        fields = ['id', 'name', 'code', 'description', 'hours_per_week', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecurrentUnitSerializer(serializers.ModelSerializer):
    """Serializer for RecurrentUnit model with nested unit data."""
    unit = CommonUnitSerializer(read_only=True)
    unit_id = serializers.IntegerField(write_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_code = serializers.CharField(source='unit.code', read_only=True)
    
    class Meta:
        model = RecurrentUnit
        fields = [
            'id', 'unit', 'unit_id', 'unit_name', 'unit_code',
            'course', 'course_code', 'course_name',
            'year_of_study', 'semester', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TrainingDataSerializer(serializers.ModelSerializer):
    """Serializer for TrainingData model with nested relationships."""
    courses = CourseSerializer(many=True, read_only=True)
    course_ids = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='courses'
    )
    lecturers = LecturerSerializer(many=True, read_only=True)
    lecturer_ids = serializers.PrimaryKeyRelatedField(
        queryset=Lecturer.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='lecturers'
    )
    departments = DepartmentSerializer(many=True, read_only=True)
    department_ids = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='departments'
    )
    common_units = CommonUnitSerializer(many=True, read_only=True)
    common_unit_ids = serializers.PrimaryKeyRelatedField(
        queryset=CommonUnit.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='common_units'
    )
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TrainingData
        fields = [
            'id', 'name', 'description',
            'courses', 'course_ids',
            'lecturers', 'lecturer_ids',
            'departments', 'department_ids',
            'common_units', 'common_unit_ids',
            'created_by', 'created_by_username',
            'created_at', 'updated_at',
            'trained_model_path', 'is_active'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads (Excel/PDF)."""
    file = serializers.FileField(
        help_text="Upload an Excel (.xlsx) or PDF file with training/timetable data"
    )
    file_type = serializers.ChoiceField(
        choices=['training_data', 'timetable_data'],
        help_text="Type of data in the file"
    )
    description = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Optional description of the uploaded data"
    )
    
    def validate_file(self, value):
        """Validate file is Excel or PDF."""
        filename = value.name.lower()
        allowed_extensions = ['.xlsx', '.xls', '.pdf', '.csv']
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"File must be one of: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 50MB")
        
        return value