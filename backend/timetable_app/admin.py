"""
Django admin configuration for timetable_app models.
"""
from django.contrib import admin
from .models import (
    User, School, Department, Program, Course, Lecturer, Room,
    CourseAllocation, StudentClass, TimeSlot, LecturerAvailability,
    Timetable, TimetableEntry, TrainingData, CommonUnit, RecurrentUnit
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'role', 'school', 'is_active')
    list_filter = ('role', 'is_active', 'school')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'school')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    def full_name(self, obj):
        return obj.get_full_name() or obj.username


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_email', 'contact_phone')
    search_fields = ('name', 'code')
    fieldsets = (
        (None, {'fields': ('name', 'code')}),
        ('Contact Info', {'fields': ('contact_email', 'contact_phone')}),
        ('Details', {'fields': ('address', 'description')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school', 'head_of_department')
    list_filter = ('school',)
    search_fields = ('name', 'code')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'level')
    list_filter = ('level', 'department__school')
    search_fields = ('name', 'code')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'program', 'semester', 'credits')
    list_filter = ('semester', 'program', 'is_core')
    search_fields = ('code', 'name')


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'employee_id', 'school', 'is_available')
    list_filter = ('school', 'department', 'is_available')
    search_fields = ('first_name', 'last_name', 'email', 'employee_id')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'capacity', 'room_type', 'school', 'is_available')
    list_filter = ('room_type', 'school', 'is_available')
    search_fields = ('building', 'room_number')


@admin.register(CourseAllocation)
class CourseAllocationAdmin(admin.ModelAdmin):
    list_display = ('course', 'lecturer', 'academic_year', 'semester')
    list_filter = ('academic_year', 'semester')
    search_fields = ('course__code', 'lecturer__last_name')


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'course', 'student_count', 'academic_year')
    list_filter = ('academic_year', 'semester')
    search_fields = ('class_name', 'course__code')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_name', 'day', 'start_time', 'end_time', 'school')
    list_filter = ('day', 'school')
    ordering = ('day', 'start_time')


@admin.register(LecturerAvailability)
class LecturerAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('lecturer', 'day', 'start_time', 'end_time', 'is_available')
    list_filter = ('day', 'is_available')
    search_fields = ('lecturer__last_name',)


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'academic_year', 'status', 'generated_by')
    list_filter = ('status', 'academic_year', 'semester')
    search_fields = ('name', 'program__code')
    readonly_fields = ('generated_at',)


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('course', 'lecturer', 'day', 'start_time', 'end_time', 'room')
    list_filter = ('day', 'timetable__academic_year')
    search_fields = ('course__code', 'lecturer__last_name')


@admin.register(TrainingData)
class TrainingDataAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'data_type', 'file_type', 'uploaded_by', 'processed')
    list_filter = ('data_type', 'file_type', 'processed', 'uploaded_at')
    search_fields = ('file_name',)
    readonly_fields = ('uploaded_at',)


@admin.register(CommonUnit)
class CommonUnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'school')
    search_fields = ('code', 'name')


@admin.register(RecurrentUnit)
class RecurrentUnitAdmin(admin.ModelAdmin):
    list_display = ('course', 'academic_year', 'semester', 'expected_enrollment')
    list_filter = ('academic_year', 'semester')
    search_fields = ('course__code',)
