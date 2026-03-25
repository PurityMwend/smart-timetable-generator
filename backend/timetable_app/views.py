"""
DRF viewsets for CRUD on all timetable models.
"""

from rest_framework import viewsets, permissions
from .models import (
    Department,
    Course,
    Lecturer,
    Room,
    TimeSlot,
    LecturerAvailability,
    TimetableEntry,
)
from .serializers import (
    DepartmentSerializer,
    CourseSerializer,
    LecturerSerializer,
    RoomSerializer,
    TimeSlotSerializer,
    LecturerAvailabilitySerializer,
    TimetableEntrySerializer,
)


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """Allow full access to ADMIN users; read-only for VIEWER users."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated
            and hasattr(request.user, 'is_admin_user')
            and request.user.is_admin_user
        )


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    search_fields = ['name', 'code']


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('department').all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_fields = ['department', 'year_of_study', 'study_mode']
    search_fields = ['name', 'code']


class LecturerViewSet(viewsets.ModelViewSet):
    queryset = Lecturer.objects.select_related('department').all()
    serializer_class = LecturerSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_fields = ['department']
    search_fields = ['name', 'employee_id']


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_fields = ['room_type', 'building']
    search_fields = ['name', 'building']


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_fields = ['day']


class LecturerAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = LecturerAvailability.objects.select_related(
        'lecturer', 'time_slot'
    ).all()
    serializer_class = LecturerAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_fields = ['lecturer', 'is_available']


class TimetableEntryViewSet(viewsets.ModelViewSet):
    queryset = TimetableEntry.objects.select_related(
        'course', 'lecturer', 'room', 'time_slot'
    ).all()
    serializer_class = TimetableEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_fields = ['time_slot__day', 'is_locked', 'course', 'lecturer', 'room']
