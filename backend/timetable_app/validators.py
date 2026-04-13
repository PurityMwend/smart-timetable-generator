"""
Custom validators for timetable models to enforce business logic constraints.
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import TimetableEntry, TimeSlot, Room, Course


# ============================================================================
# Email Domain Validators
# ============================================================================

def get_user_role_from_email(email):
    """
    Determine user role based on email domain.
    
    Returns:
        str: Role ('TIMETABLER', 'LECTURER', 'STUDENT') or None if invalid domain
    """
    from .models import User
    
    email_lower = email.lower().strip()
    
    if email_lower.endswith('@admin.cuk.ac.ke'):
        return User.Role.TIMETABLER
    elif email_lower.endswith('@staff.cuk.ac.ke'):
        return User.Role.LECTURER
    elif email_lower.endswith('@student.cuk.ac.ke'):
        return User.Role.STUDENT
    else:
        return None


def validate_cuk_email(email):
    """
    Validate that email is from an allowed CUK domain.
    Allowed domains:
    - @admin.cuk.ac.ke (Timetabler)
    - @staff.cuk.ac.ke (Lecturer)
    - @student.cuk.ac.ke (Student)
    """
    role = get_user_role_from_email(email)
    if role is None:
        raise ValidationError(
            "Email must be from one of the following domains: "
            "@admin.cuk.ac.ke, @staff.cuk.ac.ke, or @student.cuk.ac.ke"
        )
    return role


def validate_email_not_registered(email, exclude_user_id=None):
    """
    Validate that email is not already registered.
    Optionally exclude a specific user (for profile updates).
    """
    from .models import User
    
    query = User.objects.filter(email__iexact=email.strip())
    
    if exclude_user_id:
        query = query.exclude(id=exclude_user_id)
    
    if query.exists():
        raise ValidationError("This email is already registered.")


# ============================================================================
# Original Validators
# ============================================================================

def validate_time_slot(start_time, end_time):
    """Validate that start_time is before end_time."""
    if start_time >= end_time:
        raise ValidationError("Start time must be before end time.")


def validate_room_capacity(room, course):
    """Validate that room capacity is sufficient for course class size."""
    if room.capacity < course.class_size:
        raise ValidationError(
            f"Room '{room.name}' capacity ({room.capacity}) is less than "
            f"course '{course.code}' class size ({course.class_size})."
        )


def validate_no_room_double_booking(room_id, time_slot_id, exclude_entry_id=None):
    """
    Validate that a room is not double-booked at a given time slot.
    Optionally exclude a specific entry (for updates).
    """
    query = TimetableEntry.objects.filter(room_id=room_id, time_slot_id=time_slot_id)
    
    if exclude_entry_id:
        query = query.exclude(id=exclude_entry_id)
    
    if query.exists():
        raise ValidationError(
            f"Room is already booked for this time slot."
        )


def validate_no_lecturer_double_booking(lecturer_id, time_slot_id, exclude_entry_id=None):
    """
    Validate that a lecturer is not double-booked at a given time slot.
    Optionally exclude a specific entry (for updates).
    """
    query = TimetableEntry.objects.filter(lecturer_id=lecturer_id, time_slot_id=time_slot_id)
    
    if exclude_entry_id:
        query = query.exclude(id=exclude_entry_id)
    
    if query.exists():
        raise ValidationError(
            f"Lecturer is already teaching at this time slot."
        )


def validate_course_lecturer_assignment(course, lecturer):
    """
    Validate that the lecturer is assigned to teach the course
    (if course has specific lecturer assignments).
    """
    if course.lecturers.exists() and not course.lecturers.filter(id=lecturer.id).exists():
        raise ValidationError(
            f"Lecturer '{lecturer.name}' is not assigned to teach "
            f"course '{course.code}'."
        )


def validate_lecturer_availability(lecturer, time_slot):
    """Validate that lecturer is available at the given time slot."""
    from .models import LecturerAvailability
    
    # If an availability record exists, check if it's marked as unavailable
    try:
        availability = LecturerAvailability.objects.get(
            lecturer=lecturer,
            time_slot=time_slot
        )
        if not availability.is_available:
            raise ValidationError(
                f"Lecturer '{lecturer.name}' is not available during "
                f"{time_slot.get_day_display()} {time_slot.start_time}-{time_slot.end_time}."
            )
    except LecturerAvailability.DoesNotExist:
        # No availability record means the lecturer is available by default
        pass


def validate_timetable_entry_constraints(course, lecturer, room, time_slot, exclude_entry_id=None):
    """
    Validate all timetable entry constraints.
    """
    # Check room capacity
    validate_room_capacity(room, course)
    
    # Check lecturer assignment
    validate_course_lecturer_assignment(course, lecturer)
    
    # Check lecturer availability
    validate_lecturer_availability(lecturer, time_slot)
    
    # Check for double bookings
    validate_no_room_double_booking(room.id, time_slot.id, exclude_entry_id)
    validate_no_lecturer_double_booking(lecturer.id, time_slot.id, exclude_entry_id)
