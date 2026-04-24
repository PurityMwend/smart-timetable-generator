"""
Serializers for timetable_app models - convert models to/from JSON.
"""
from rest_framework import serializers
from .models import (
    User, School, Department, Program, Course, Lecturer, Room,
    CourseAllocation, StudentClass, TimeSlot, LecturerAvailability,
    Timetable, TimetableEntry, TrainingData, CommonUnit, RecurrentUnit,
    Unit, CourseUnit
)



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'school')
        read_only_fields = ('id',)


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ('id', 'name', 'code', 'description', 'address', 'contact_email', 'contact_phone')
        read_only_fields = ('id',)


class DepartmentSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = Department
        fields = ('id', 'name', 'code', 'school', 'school_name', 'head_of_department', 'email')
        read_only_fields = ('id',)


class ProgramSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Program
        fields = ('id', 'name', 'code', 'department', 'department_name', 'level', 'duration_semesters')
        read_only_fields = ('id',)


class CourseSerializer(serializers.ModelSerializer):
    program_code = serializers.CharField(source='program.code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Course
        fields = ('id', 'code', 'name', 'department', 'department_name', 'program', 'program_code', 'credits', 'semester', 'is_core')
        read_only_fields = ('id',)
        extra_kwargs = {
            'program': {'required': False, 'allow_null': True}
        }



class LecturerSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = Lecturer
        fields = ('id', 'first_name', 'last_name', 'email', 'employee_id', 'school', 'school_name', 'is_available')
        read_only_fields = ('id',)


class RoomSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = Room
        fields = ('id', 'building', 'room_number', 'room_type', 'capacity', 'school', 'school_name', 'is_available')
        read_only_fields = ('id',)


class CourseAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseAllocation
        fields = ('id', 'course', 'lecturer', 'semester', 'academic_year', 'hours_per_week')
        read_only_fields = ('id',)


class StudentClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentClass
        fields = ('id', 'program', 'course', 'class_name', 'semester', 'academic_year', 'student_count')
        read_only_fields = ('id',)


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ('id', 'school', 'day', 'start_time', 'end_time', 'slot_name', 'is_available')
        read_only_fields = ('id',)


class LecturerAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LecturerAvailability
        fields = ('id', 'lecturer', 'day', 'start_time', 'end_time', 'is_available', 'reason')
        read_only_fields = ('id',)


class TimetableSerializer(serializers.ModelSerializer):
    program_code = serializers.CharField(source='program.code', read_only=True)
    
    class Meta:
        model = Timetable
        fields = ('id', 'name', 'program', 'program_code', 'semester', 'academic_year', 'status', 'generated_by')
        read_only_fields = ('id', 'generated_by')


class TimetableEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimetableEntry
        fields = ('id', 'timetable', 'student_class', 'course', 'lecturer', 'room', 'day', 'start_time', 'end_time', 'duration_hours')
        read_only_fields = ('id',)


class TrainingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingData
        fields = ('id', 'school', 'file_name', 'file_type', 'data_type', 'file_size', 'uploaded_by', 'processed')
        read_only_fields = ('id', 'uploaded_by')


class CommonUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonUnit
        fields = ('id', 'school', 'code', 'name', 'description', 'programs')
        read_only_fields = ('id',)


class RecurrentUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrentUnit
        fields = ('id', 'course', 'academic_year', 'semester', 'expected_enrollment', 'notes')
        read_only_fields = ('id',)


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ('id', 'code', 'name', 'description', 'credits', 'hours_per_week', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class CourseUnitSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source='unit.code', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    
    class Meta:
        model = CourseUnit
        fields = ('id', 'course', 'unit', 'unit_code', 'unit_name', 'year_of_study', 'semester', 'is_core')
        read_only_fields = ('id',)

