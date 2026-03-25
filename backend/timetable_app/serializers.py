"""
DRF serializers for all timetable models.
"""

from rest_framework import serializers
from .models import (
    User,
    Department,
    Course,
    Lecturer,
    Room,
    TimeSlot,
    LecturerAvailability,
    TimetableEntry,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


class LecturerSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Lecturer
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class TimeSlotSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = TimeSlot
        fields = '__all__'


class LecturerAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LecturerAvailability
        fields = '__all__'


class TimetableEntrySerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    lecturer_name = serializers.CharField(source='lecturer.name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    time_slot_display = serializers.StringRelatedField(source='time_slot', read_only=True)

    class Meta:
        model = TimetableEntry
        fields = '__all__'
