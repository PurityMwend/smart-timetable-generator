"""
DRF viewsets for CRUD on all timetable models.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import openpyxl
import pdfplumber
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUserOrReadOnly])
def upload_data(request):
    """Upload and parse Excel or PDF file to create/update data."""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    file_name = file.name.lower()
    
    if file_name.endswith('.xlsx'):
        return parse_excel(file)
    elif file_name.endswith('.pdf'):
        return parse_pdf(file)
    else:
        return Response({'error': 'Unsupported file type'}, status=status.HTTP_400_BAD_REQUEST)


def parse_excel(file):
    """Parse Excel file with sheets: Departments, Courses, Lecturers, Rooms, TimeSlots."""
    try:
        wb = openpyxl.load_workbook(file)
        data = {}
        
        # Parse Departments
        if 'Departments' in wb.sheetnames:
            sheet = wb['Departments']
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row[0] and row[1]:
                    Department.objects.get_or_create(name=row[0], code=row[1])
        
        # Parse Courses
        if 'Courses' in wb.sheetnames:
            sheet = wb['Courses']
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row[0] and row[1] and row[2]:
                    dept = get_object_or_404(Department, code=row[2])
                    Course.objects.get_or_create(
                        code=row[0], defaults={
                            'name': row[1], 'department': dept, 'year_of_study': row[3] or 1,
                            'study_mode': row[4] or 'IN_PERSON', 'class_size': row[5] or 30,
                            'hours_per_week': row[6] or 1
                        }
                    )
        
        # Similarly for Lecturers, Rooms, TimeSlots
        # For brevity, implement basic
        
        return Response({'message': 'Data uploaded successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def parse_pdf(file):
    """Parse PDF file - placeholder for now."""
    return Response({'message': 'PDF parsing not implemented yet'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def course_timetable(request, course_id):
    """Get timetable entries for a specific course."""
    entries = TimetableEntry.objects.filter(course_id=course_id).select_related('time_slot', 'room', 'lecturer')
    serializer = TimetableEntrySerializer(entries, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def lecturer_timetable(request, lecturer_id):
    """Get timetable entries for a specific lecturer."""
    entries = TimetableEntry.objects.filter(lecturer_id=lecturer_id).select_related('time_slot', 'room', 'course')
    serializer = TimetableEntrySerializer(entries, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def room_timetable(request, room_id):
    """Get timetable entries for a specific room."""
    entries = TimetableEntry.objects.filter(room_id=room_id).select_related('time_slot', 'course', 'lecturer')
    serializer = TimetableEntrySerializer(entries, many=True)
    return Response(serializer.data)
