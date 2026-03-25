from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

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


# ---------------------------------------------------------------------------
# Custom User admin
# ---------------------------------------------------------------------------

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


# ---------------------------------------------------------------------------
# Domain model admins
# ---------------------------------------------------------------------------

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('name', 'code')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'year_of_study', 'study_mode', 'class_size')
    list_filter = ('department', 'year_of_study', 'study_mode')
    search_fields = ('code', 'name')


@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_id', 'department', 'email')
    list_filter = ('department',)
    search_fields = ('name', 'employee_id', 'email')
    filter_horizontal = ('courses',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'capacity', 'room_type')
    list_filter = ('room_type', 'building')
    search_fields = ('name', 'building')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('day', 'start_time', 'end_time')
    list_filter = ('day',)


@admin.register(LecturerAvailability)
class LecturerAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('lecturer', 'time_slot', 'is_available')
    list_filter = ('is_available', 'lecturer')


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('course', 'lecturer', 'room', 'time_slot', 'is_locked')
    list_filter = ('is_locked', 'time_slot__day')
    search_fields = ('course__code', 'course__name', 'lecturer__name', 'room__name')
