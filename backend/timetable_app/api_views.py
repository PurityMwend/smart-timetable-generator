"""
API views for timetable_app - REST API endpoints.
Comprehensive CRUD operations for all resources.
"""
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import (
    User, School, Department, Program, Course, Lecturer, Room,
    CourseAllocation, StudentClass, TimeSlot, LecturerAvailability,
    Timetable, TimetableEntry, TrainingData, CommonUnit, RecurrentUnit,
    Unit, CourseUnit,
)

from .serializers import (
    UserSerializer, SchoolSerializer, DepartmentSerializer, ProgramSerializer,
    CourseSerializer, LecturerSerializer, RoomSerializer, CourseAllocationSerializer,
    StudentClassSerializer, TimeSlotSerializer, LecturerAvailabilitySerializer,
    TimetableSerializer, TimetableEntrySerializer, TrainingDataSerializer,
    CommonUnitSerializer, RecurrentUnitSerializer
)


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user."""
    try:
        User = get_user_model()
        
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        # Validation
        if not username or not email or not password or not password_confirm:
            return Response(
                {'error': 'Username, email, password, and password confirmation are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != password_confirm:
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(username) < 3:
            return Response(
                {'error': 'Username must be at least 3 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user as admin (Timetabler) by default
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='admin'
        )
        
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'message': 'User registered successfully. Please log in.'
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Authenticate user and create session."""
    try:
        # Get credentials from request
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        if not username_or_email or not password:
            return Response(
                {'error': 'Username/email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        User = get_user_model()
        user = None
        
        # Try to authenticate by username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If not found, try to find by email
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        # If still not found, try to find by username containing the input (case-insensitive search)
        if user is None:
            try:
                user_obj = User.objects.get(username__iexact=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                return Response(
                    {'error': f'User with username/email "{username_or_email}" not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        if user is None:
            return Response(
                {'error': 'Password is incorrect'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is active
        if not user.is_active:
            return Response(
                {'error': 'User account is disabled. Please contact support.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create session
        login(request, user)
        
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'school_id': user.school.id if user.school else None,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'message': 'Login successful'
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Login error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout the authenticated user."""
    try:
        logout(request)
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user's information."""
    try:
        user = request.user
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'school': user.school.id if user.school else None,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """Get CSRF token for forms."""
    from django.middleware.csrf import get_token
    try:
        csrf_token = get_token(request)
        return Response(
            {
                'csrf_token': csrf_token,
                'message': 'CSRF token retrieved successfully'
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for the authenticated user."""
    try:
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return Response(
                {'error': 'Old password, new password, and confirmation are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify old password
        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if new passwords match
        if new_password != confirm_password:
            return Response(
                {'error': 'New passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check password strength (at least 8 characters)
        if len(new_password) < 8:
            return Response(
                {'error': 'New password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Change password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# SCHOOL ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_schools(request):
    """List all schools or create a new school."""
    if request.method == 'GET':
        schools = School.objects.all()
        serializer = SchoolSerializer(schools, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_school(request, pk):
    """Retrieve, update, or delete a school."""
    school = get_object_or_404(School, pk=pk)
    
    if request.method == 'GET':
        serializer = SchoolSerializer(school)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = SchoolSerializer(school, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        school.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def school_departments(request, pk):
    """List departments within a school. Supports ?q= search."""
    school = get_object_or_404(School, pk=pk)
    qs = school.departments.all()
    q = request.query_params.get('q', '')
    if q:
        qs = qs.filter(name__icontains=q)
    serializer = DepartmentSerializer(qs, many=True)
    return Response(serializer.data)


# ============================================================================
# DEPARTMENT ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_departments(request):
    """List all departments or create a new department."""
    if request.method == 'GET':
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_department(request, pk):
    """Retrieve, update, or delete a department."""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'GET':
        serializer = DepartmentSerializer(department)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = DepartmentSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_courses(request, pk):
    """List courses that belong to a department directly, or via any of its programs."""
    department = get_object_or_404(Department, pk=pk)
    qs = Course.objects.filter(
        Q(department=department) |
        Q(program__department=department)
    ).distinct()
    serializer = CourseSerializer(qs, many=True)
    return Response(serializer.data)


# ============================================================================
# PROGRAM ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_programs(request):
    """List all programs or create a new program."""
    if request.method == 'GET':
        programs = Program.objects.all()
        serializer = ProgramSerializer(programs, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ProgramSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_program(request, pk):
    """Retrieve, update, or delete a program."""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'GET':
        serializer = ProgramSerializer(program)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProgramSerializer(program, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        program.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# COURSE ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_courses(request):
    """List all courses or create a new course."""
    if request.method == 'GET':
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_course(request, pk):
    """Retrieve, update, or delete a course."""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'GET':
        serializer = CourseSerializer(course)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_lecturers(request, pk):
    """Get all lecturers assigned to a course."""
    course = get_object_or_404(Course, pk=pk)
    lecturers = Lecturer.objects.filter(course_allocations__course=course).distinct()
    serializer = LecturerSerializer(lecturers, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_timetable(request, pk):
    """Get timetable entries for a course."""
    course = get_object_or_404(Course, pk=pk)
    entries = TimetableEntry.objects.filter(course=course)
    serializer = TimetableEntrySerializer(entries, many=True)
    return Response(serializer.data)


# ============================================================================
# LECTURER ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_lecturers(request):
    """List all lecturers or create a new lecturer."""
    if request.method == 'GET':
        lecturers = Lecturer.objects.all()
        serializer = LecturerSerializer(lecturers, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = LecturerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_lecturer(request, pk):
    """Retrieve, update, or delete a lecturer."""
    lecturer = get_object_or_404(Lecturer, pk=pk)
    
    if request.method == 'GET':
        serializer = LecturerSerializer(lecturer)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = LecturerSerializer(lecturer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        lecturer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lecturer_timetable(request, pk):
    """Get timetable entries for a lecturer."""
    lecturer = get_object_or_404(Lecturer, pk=pk)
    entries = TimetableEntry.objects.filter(lecturer=lecturer)
    serializer = TimetableEntrySerializer(entries, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lecturer_availability(request, pk):
    """Get/create availability for a lecturer."""
    lecturer = get_object_or_404(Lecturer, pk=pk)
    
    if request.method == 'GET':
        availabilities = LecturerAvailability.objects.filter(lecturer=lecturer)
        serializer = LecturerAvailabilitySerializer(availabilities, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data.copy()
        data['lecturer'] = pk
        serializer = LecturerAvailabilitySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# ROOM ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_rooms(request):
    """List all rooms or create a new room."""
    if request.method == 'GET':
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_room(request, pk):
    """Retrieve, update, or delete a room."""
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'GET':
        serializer = RoomSerializer(room)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = RoomSerializer(room, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_availability(request, pk):
    """Get availability/schedule for a room."""
    room = get_object_or_404(Room, pk=pk)
    entries = TimetableEntry.objects.filter(room=room)
    serializer = TimetableEntrySerializer(entries, many=True)
    return Response(serializer.data)


# ============================================================================
# TIME SLOT ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
def list_create_time_slots(request):
    """List all time slots or create a new one."""
    if request.method == 'GET':
        school_id = request.query_params.get('school')
        if school_id:
            slots = TimeSlot.objects.filter(school_id=school_id)
        elif hasattr(request.user, 'school') and request.user.school:
            slots = TimeSlot.objects.filter(school=request.user.school)
        else:
            slots = TimeSlot.objects.all()
        serializer = TimeSlotSerializer(slots, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TimeSlotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def retrieve_update_delete_time_slot(request, pk):
    """Retrieve, update, or delete a time slot."""
    slot = get_object_or_404(TimeSlot, pk=pk)

    if request.method == 'GET':
        serializer = TimeSlotSerializer(slot)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = TimeSlotSerializer(slot, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# STUDENT/CLASS ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_student_classes(request):
    """List all student classes or create a new one."""
    if request.method == 'GET':
        classes = StudentClass.objects.all()
        serializer = StudentClassSerializer(classes, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = StudentClassSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_student_class(request, pk):
    """Retrieve, update, or delete a student class."""
    student_class = get_object_or_404(StudentClass, pk=pk)
    
    if request.method == 'GET':
        serializer = StudentClassSerializer(student_class)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = StudentClassSerializer(student_class, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        student_class.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_class_timetable(request, pk):
    """Get timetable for a student class."""
    student_class = get_object_or_404(StudentClass, pk=pk)
    entries = TimetableEntry.objects.filter(student_class=student_class)
    serializer = TimetableEntrySerializer(entries, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_class_enrollments(request, pk):
    """Get enrollment information for a student class."""
    student_class = get_object_or_404(StudentClass, pk=pk)
    serializer = StudentClassSerializer(student_class)
    return Response({
        'class': serializer.data,
        'total_students': student_class.student_count,
        'course': student_class.course.code,
        'program': student_class.program.code
    })


# ============================================================================
# TIMETABLE ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_timetables(request):
    """List all timetables or create a new one."""
    if request.method == 'GET':
        timetables = Timetable.objects.all()
        serializer = TimetableSerializer(timetables, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['generated_by'] = request.user.id
        serializer = TimetableSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_timetable(request, pk):
    """Retrieve, update, or delete a timetable."""
    timetable = get_object_or_404(Timetable, pk=pk)
    
    if request.method == 'GET':
        serializer = TimetableSerializer(timetable)
        entries = timetable.entries.all()
        entries_serializer = TimetableEntrySerializer(entries, many=True)
        return Response({
            'timetable': serializer.data,
            'entries': entries_serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = TimetableSerializer(timetable, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        timetable.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_timetable(request, pk):
    """Generate a timetable using OR-Tools + ML optimizer."""
    try:
        timetable = get_object_or_404(Timetable, pk=pk)

        # Resolve school from the program chain
        school = timetable.program.department.school

        courses = list(Course.objects.filter(
            program=timetable.program,
            semester=timetable.semester,
        ).select_related('program__department__school'))

        lecturers = list(Lecturer.objects.filter(
            school=school,
            is_available=True,
        ).select_related('department'))

        rooms = list(Room.objects.filter(
            school=school,
            is_available=True,
        ))

        time_slots = list(TimeSlot.objects.filter(
            school=school,
            is_available=True,
        ).order_by('day', 'start_time'))

        if not courses:
            return Response({'error': 'No courses found for this program/semester.'}, status=status.HTTP_400_BAD_REQUEST)
        if not rooms:
            return Response({'error': 'No rooms available.'}, status=status.HTTP_400_BAD_REQUEST)
        if not time_slots:
            return Response({'error': 'No time slots defined.'}, status=status.HTTP_400_BAD_REQUEST)
        if not lecturers:
            return Response({'error': 'No lecturers available.'}, status=status.HTTP_400_BAD_REQUEST)

        # Clear existing entries for this timetable before re-generating
        TimetableEntry.objects.filter(timetable=timetable).delete()

        # Train ML optimizer on historical data
        from .services.ml_optimizer import MLOptimizer
        optimizer = MLOptimizer()
        optimizer.train()

        from .services.scheduler import TimetableScheduler
        scheduler = TimetableScheduler(
            courses=courses,
            lecturers=lecturers,
            rooms=rooms,
            time_slots=time_slots,
            timetable=timetable,
            ml_optimizer=optimizer,
        )
        entries = scheduler.generate()

        # Mark timetable as published
        timetable.status = 'published'
        timetable.save(update_fields=['status', 'updated_at'])

        serializer = TimetableEntrySerializer(entries, many=True)
        return Response({
            'message': f'Timetable generated successfully with {len(entries)} entries.',
            'timetable_id': timetable.id,
            'status': 'published',
            'entries': serializer.data,
            'entry_count': len(entries),
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_timetable(request, pk):
    """Export timetable as Excel (.xlsx) or PDF."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from django.http import HttpResponse
    import io

    timetable = get_object_or_404(Timetable, pk=pk)
    fmt = request.GET.get('format', 'excel').lower()
    entries = list(
        TimetableEntry.objects.filter(timetable=timetable)
        .select_related('course', 'lecturer', 'room', 'student_class')
        .order_by('day', 'start_time')
    )

    DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    DAY_LABELS = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday',
                  'THU': 'Thursday', 'FRI': 'Friday', 'SAT': 'Saturday'}

    if fmt == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{timetable.name[:28]}"

        # Header style
        hdr_font = Font(bold=True, color='FFFFFF')
        hdr_fill = PatternFill('solid', fgColor='1a73e8')
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # Collect all unique time labels
        time_labels = sorted(
            set(f"{e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')}" for e in entries)
        )
        if not time_labels:
            time_labels = ['No slots']

        # Write header row
        ws.cell(row=1, column=1, value='Time / Day').font = hdr_font
        ws.cell(row=1, column=1).fill = hdr_fill
        ws.cell(row=1, column=1).alignment = center
        for col, day in enumerate(DAYS, start=2):
            cell = ws.cell(row=1, column=col, value=DAY_LABELS[day])
            cell.font = hdr_font
            cell.fill = hdr_fill
            cell.alignment = center
            ws.column_dimensions[cell.column_letter].width = 22

        # Build lookup: (day, time_label) -> entry text
        lookup = {}
        for e in entries:
            key = (e.day, f"{e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')}")
            lookup[key] = (
                f"{e.course.code}\n{e.course.name}\n"
                f"Lec: {e.lecturer.first_name} {e.lecturer.last_name}\n"
                f"Room: {e.room.building}-{e.room.room_number}"
            )

        for row_idx, tl in enumerate(time_labels, start=2):
            ws.cell(row=row_idx, column=1, value=tl).alignment = center
            ws.row_dimensions[row_idx].height = 60
            for col_idx, day in enumerate(DAYS, start=2):
                cell = ws.cell(row=row_idx, column=col_idx, value=lookup.get((day, tl), ''))
                cell.alignment = center
                cell.border = border

        ws.column_dimensions['A'].width = 18

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        fname = f"timetable_{timetable.id}.xlsx"
        response = HttpResponse(
            buf.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{fname}"'
        return response

    elif fmt == 'pdf':
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                                leftMargin=1*cm, rightMargin=1*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"<b>{timetable.name}</b>", styles['Title']))
        elements.append(Paragraph(
            f"{timetable.program.name} | Semester {timetable.semester} | {timetable.academic_year}",
            styles['Normal'],
        ))
        elements.append(Spacer(1, 0.4*cm))

        time_labels = sorted(
            set(f"{e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')}" for e in entries)
        )
        lookup = {}
        for e in entries:
            key = (e.day, f"{e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')}")
            lookup[key] = (
                f"{e.course.code}\n{e.lecturer.first_name[0]}. {e.lecturer.last_name}\n"
                f"{e.room.building}-{e.room.room_number}"
            )

        header_row = ['Time'] + [DAY_LABELS[d] for d in DAYS]
        table_data = [header_row]
        for tl in time_labels:
            row = [tl] + [lookup.get((day, tl), '') for day in DAYS]
            table_data.append(row)

        if not time_labels:
            table_data.append(['No entries generated yet'] + ['' for _ in DAYS])

        col_widths = [2.8*cm] + [3.8*cm] * 6
        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e8f0fe')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#f5f8ff')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWHEIGHT', (0, 1), (-1, -1), 48),
        ]))
        elements.append(tbl)

        doc.build(elements)
        buf.seek(0)
        fname = f"timetable_{timetable.id}.pdf"
        response = HttpResponse(buf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{fname}"'
        return response

    return Response({'error': f'Unknown format: {fmt}. Use excel or pdf.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_timetable(request):
    """Import/parse a sample data file (alias for upload_sample_data)."""
    return upload_sample_data(request)


# ============================================================================
# TIMETABLE ENTRY ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
def list_create_timetable_entries(request):
    """List all timetable entries or create a new one."""
    if request.method == 'GET':
        school_id = request.query_params.get('school')
        if school_id:
            entries = TimetableEntry.objects.filter(timetable__program__department__school_id=school_id)
        elif hasattr(request.user, 'school') and request.user.school:
            entries = TimetableEntry.objects.filter(timetable__program__department__school=request.user.school)
        else:
            entries = TimetableEntry.objects.all()
        serializer = TimetableEntrySerializer(entries, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TimetableEntrySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def retrieve_update_delete_timetable_entry(request, pk):
    """Retrieve, update, or delete a timetable entry."""
    entry = get_object_or_404(TimetableEntry, pk=pk)

    if request.method == 'GET':
        serializer = TimetableEntrySerializer(entry)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = TimetableEntrySerializer(entry, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# UPLOAD SAMPLE DATA
# ============================================================================

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_sample_data(request):
    """
    Upload a PDF or Excel file to seed the database.

    Returns a structured summary of entities created/updated/errored.
    """
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided. Send file as multipart/form-data.'}, status=status.HTTP_400_BAD_REQUEST)

    # Optionally link to the logged-in user's school
    school = getattr(request.user, 'school', None)

    from .services.file_parser import FileParser
    success, message, summary = FileParser.parse_file(file, school=school)

    if success:
        return Response({'message': message, 'summary': summary}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message, 'summary': summary}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def download_sample_template(request):
    """
    Generate a sample Excel template that exactly matches the flat timetable
    format shown in the interface: COURSE, UNIT CODE, UNIT NAME, C.S,
    LECTURER, DAY, TIME, M.O.S, ROOM.
    """
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    import io

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Timetable"

    # ── Colours ──────────────────────────────────────────────────────────────
    header_fill   = PatternFill("solid", fgColor="FFCCCC")   # Pink header row
    header_font   = Font(bold=True, color="000000", size=10)
    data_font     = Font(size=9)
    center_align  = Alignment(horizontal="center", vertical="center")
    left_align    = Alignment(horizontal="left",   vertical="center")
    thin_border   = Border(
        left=Side(style="thin"),  right=Side(style="thin"),
        top=Side(style="thin"),   bottom=Side(style="thin"),
    )

    # ── Column widths ─────────────────────────────────────────────────────────
    col_widths = [10, 12, 38, 6, 20, 12, 18, 14, 14]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    HEADERS = ["COURSE", "UNIT CODE", "UNIT NAME", "C.S",
               "LECTURER", "DAY", "TIME", "M.O.S", "ROOM"]

    def write_header_row(ws, row_num):
        for col, h in enumerate(HEADERS, 1):
            cell = ws.cell(row=row_num, column=col, value=h)
            cell.fill   = header_fill
            cell.font   = header_font
            cell.alignment = center_align
            cell.border = thin_border
        ws.row_dimensions[row_num].height = 20

    def write_data_row(ws, row_num, values):
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row_num, column=col, value=val)
            cell.font   = data_font
            cell.border = thin_border
            cell.alignment = left_align if col in (3, 5) else center_align

    # ─────────────────────────────────────────────────────────────────────────
    # Year 1 Semester 2 block
    # ─────────────────────────────────────────────────────────────────────────
    current_row = 1
    write_header_row(ws, current_row)

    y1_s2_data = [
        ["BIT Y1 S2", "BENT 1207", "ENTREPRENEURSHIP SKILLS",          107, "Dr. Kiura",           "FRIDAY",    "7:00AM-10:00AM",  "Online",        "Zoom"],
        ["BIT Y1 S2", "BMAT 1205", "CALCULUS I",                        107, "Dr. Paul Wachira",    "FRIDAY",    "4:00PM-7:00PM",   "Face to Face",  "H4"],
        ["BIT Y1 S2", "BCIT 1202", "DATA COMMUNICATION AND NETWORKS",  107, "Dr. Charles Katila",  "TUESDAY",   "1:00PM-4:00PM",   "Online",        "Zoom"],
        ["BIT Y1 S2", "BCIT 1210", "DATABASE MANAGEMENT SYSTEMS",      107, "Watson Musyoki",      "MONDAY",    "1:00PM-4:00PM",   "Face to Face",  "NB RM B"],
        ["BIT Y1 S2", "BMAT 1204", "DISCRETE MATHEMATICS",             107, "David Ngari",         "TUESDAY",   "4:00PM-7:00PM",   "Face to Face",  "LTA 2"],
        ["BIT Y1 S2", "BCSC 1204", "DATA STRUCTURES AND ALGORITHMS",   107, "Silas Maiya",         "THURSDAY",  "1:00PM-4:00PM",   "Face to Face",  "NB RM C"],
        ["BIT Y1 S2", "BCSE 1203", "STRUCTURED PROGRAMMING LAB",       107, "Plus Sigel",          "FRIDAY",    "1:00PM-4:00PM",   "Face to Face",  "NB RM D"],
    ]
    for values in y1_s2_data:
        current_row += 1
        write_data_row(ws, current_row, values)

    # ─────────────────────────────────────────────────────────────────────────
    # Empty separator row + Year 2 block
    # ─────────────────────────────────────────────────────────────────────────
    current_row += 2
    write_header_row(ws, current_row)

    y2_s2_data = [
        ["BIT Y2 S2", "BCIT 2230", "ADVANCED OPERATING SYSTEMS",           117, "Michael Ndege",      "MONDAY",   "1:00PM-4:00PM",  "Face to Face", "NB RM D"],
        ["BIT Y2 S2", "BCSC 2205", "COMPUTER AIDED ART AND DESIGN",        117, "Dr. James Obuhuma",  "FRIDAY",   "7:00AM-10:00AM", "Face to Face", "NORDIC HALL"],
        ["BIT Y2 S2", "BCIT 2217", "OBJECT ORIENTED PROGRAMMING II",       117, "Edward Kariuki",     "THURSDAY", "10:00AM-1:00PM", "Face to Face", "HALL 1"],
        ["BIT Y2 S2", "BPHY 1204", "DIGITAL LOGIC AND ELECTRONICS",        117, "Dr. Wycliffe Omwansu","MONDAY",  "10:00AM-1:00PM", "Face to Face", "LTA 11/12"],
        ["BIT Y2 S2", "BSTA 1203", "PROBABILITY AND STATISTICS I",         117, "Mary Kamino",        "FRIDAY",   "10:00AM-1:00PM", "Face to Face", "HALL 1"],
        ["BIT Y2 S2", "BCIT 2214", "SOFTWARE ENGINEERING",                 117, "Bostone Ochieng",    "THURSDAY", "1:00PM-4:00PM",  "Face to Face", "NB RM B"],
        ["BIT Y2 S2", "BCIT 2213", "NETWORKS AND SYSTEMS ADMINISTRATION",  117, "Wilson Muange",      "TUESDAY",  "1:00PM-4:00PM",  "Face to Face", "NB RM D"],
    ]
    for values in y2_s2_data:
        current_row += 1
        write_data_row(ws, current_row, values)

    # ─────────────────────────────────────────────────────────────────────────
    # Year 3 block
    # ─────────────────────────────────────────────────────────────────────────
    current_row += 2
    write_header_row(ws, current_row)

    y3_s2_data = [
        ["BIT Y3 S2", "BCIT 3238", "MOBILE APPLICATION DEVELOPMENT",       100, "Jonah Marwa",         "FRIDAY",     "1:00PM-4:00PM",  "Online",        "Zoom"],
        ["BIT Y3 S2", "BCIT 3237", "ELECTRONIC COMMERCE",                  100, "Salome Mwangi",       "WEDNESDAY",  "1:00PM-4:00PM",  "Face to Face",  "NB RM C"],
        ["BIT Y3 S2", "BCIT 3242", "ADVANCED DATABASE MANAGEMENT SYSTEMS", 100, "Stanley Munga",       "WEDNESDAY",  "4:00PM-7:00PM",  "Face to Face",  "LTA 1"],
        ["BIT Y3 S2", "BCSC 3225", "ARTIFICIAL INTELLIGENCE",              100, "Dr. James Obuhuma",   "FRIDAY",     "10:00AM-1:00PM", "Face to Face",  "NORDIC HALL"],
        ["BIT Y3 S2", "BCIT 3260", "RESEARCH METHODS FOR IT",              100, "Peter Wairigu",       "THURSDAY",   "1:00PM-4:00PM",  "Online",        "Zoom"],
        ["BIT Y3 S2", "BCIT 3265", "DISTRIBUTED SYSTEMS",                  100, "Michael Ndege",       "MONDAY",     "4:00PM-7:00PM",  "Face to Face",  "NB RM C"],
        ["BIT Y3 S2", "BCIT 3244", "MULTIMEDIA SYSTEMS",                   100, "Luke Okelo",          "THURSDAY",   "4:00PM-7:00PM",  "Face to Face",  "LTA 7"],
    ]
    for values in y3_s2_data:
        current_row += 1
        write_data_row(ws, current_row, values)

    # Freeze top row
    ws.freeze_panes = "A2"

    # ─────────────────────────────────────────────────────────────────────────
    # Second sheet: Instructions
    # ─────────────────────────────────────────────────────────────────────────
    ws2 = wb.create_sheet("Instructions")
    instructions = [
        ["Smart Timetable Generator — Upload Format Guide"],
        [""],
        ["COLUMN", "DESCRIPTION", "EXAMPLE"],
        ["COURSE",     "Program and year (stays same per group)", "BIT Y1 S2"],
        ["UNIT CODE",  "Course/unit code",                        "BCIT 1202"],
        ["UNIT NAME",  "Full name of the unit",                   "Data Communication and Computer Networks"],
        ["C.S",        "Class size (number of students)",         "107"],
        ["LECTURER",   "Lecturer full name (with title)",         "Dr. Charles Katila"],
        ["DAY",        "Day of the week (full or abbreviated)",   "TUESDAY or TUE"],
        ["TIME",       "Time range in 12-hour format",            "1:00PM-4:00PM or 13:00-16:00"],
        ["M.O.S",      "Mode of Study",                           "Face to Face, Online, or Hybrid"],
        ["ROOM",       "Room/Venue name",                         "NB RM B, Zoom, HALL 1"],
        [""],
        ["NOTES:"],
        ["- You can have multiple 'header rows' (COURSE, UNIT CODE, ...) to separate year groups"],
        ["- Header rows are auto-detected and skipped"],
        ["- Empty rows between groups are fine"],
        ["- The system will auto-create Rooms, Lecturers, Time Slots and Courses from this data"],
    ]
    ws2.column_dimensions['A'].width = 14
    ws2.column_dimensions['B'].width = 38
    ws2.column_dimensions['C'].width = 40
    for row in instructions:
        ws2.append(row)
    ws2['A1'].font = Font(bold=True, size=13)
    ws2['A3'].font = Font(bold=True)
    ws2['B3'].font = Font(bold=True)
    ws2['C3'].font = Font(bold=True)

    # ── Output ──────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="timetable_template.xlsx"'
    return response


# ============================================================================
# QUICK GENERATE (school-wide, no pre-existing Timetable record required)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_timetable_quick(request):
    """
    Quick-fire timetable generation for the TimetableGenerator page.

    Uses the authenticated user's school.  Finds or creates a draft Timetable
    for the first available program, then runs the scheduler.
    """
    try:
        from .services.ml_optimizer import MLOptimizer
        from .services.scheduler import TimetableScheduler

        school = getattr(request.user, 'school', None)
        if school is None:
            # Fall back to any school in the DB
            school = School.objects.first()
        if school is None:
            return Response({'error': 'No school configured. Please create a school first.'}, status=status.HTTP_400_BAD_REQUEST)

        # Pick first available program (or the one requested)
        program_id = request.data.get('program_id')
        if program_id:
            program = get_object_or_404(Program, pk=program_id)
        else:
            program = Program.objects.filter(department__school=school).first()
        if program is None:
            return Response({'error': 'No programs found for this school.'}, status=status.HTTP_400_BAD_REQUEST)

        semester = int(request.data.get('semester', 1))
        academic_year = request.data.get('academic_year', '2024/2025')

        # Find or create a draft timetable
        timetable, created = Timetable.objects.get_or_create(
            program=program,
            semester=semester,
            academic_year=academic_year,
            defaults={'name': f'{program.code} Sem{semester} {academic_year}', 'generated_by': request.user},
        )
        # Always reset to draft before re-generating
        timetable.status = 'draft'
        timetable.save(update_fields=['status', 'updated_at'])

        courses = list(Course.objects.filter(program=program, semester=semester)
                       .select_related('program__department__school'))
        lecturers = list(Lecturer.objects.filter(school=school, is_available=True)
                         .select_related('department'))
        rooms = list(Room.objects.filter(school=school, is_available=True))
        time_slots = list(TimeSlot.objects.filter(school=school, is_available=True)
                          .order_by('day', 'start_time'))

        missing = []
        if not courses:    missing.append('courses')
        if not lecturers:  missing.append('lecturers')
        if not rooms:      missing.append('rooms')
        if not time_slots: missing.append('time_slots')
        if missing:
            return Response(
                {'error': f"Missing data: {', '.join(missing)}. Please upload sample data first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Clear previous entries for this timetable
        TimetableEntry.objects.filter(timetable=timetable).delete()

        optimizer = MLOptimizer()
        optimizer.train()

        scheduler = TimetableScheduler(
            courses=courses,
            lecturers=lecturers,
            rooms=rooms,
            time_slots=time_slots,
            timetable=timetable,
            ml_optimizer=optimizer,
        )
        entries = scheduler.generate()

        if not entries:
            return Response({
                'error': 'Solver could not find a feasible schedule. This usually happens due to over-constraining (e.g., more courses than available room slots, or lecturers having many unavailability windows).',
                'details': {
                    'courses_count': len(courses),
                    'rooms_count': len(rooms),
                    'time_slots_count': len(time_slots),
                    'lecturers_count': len(lecturers)
                }
            }, status=status.HTTP_409_CONFLICT)

        timetable.status = 'published'
        timetable.save(update_fields=['status', 'updated_at'])

        serializer = TimetableEntrySerializer(entries, many=True)
        return Response({
            'message': f'Timetable generated with {len(entries)} sessions.',
            'timetable_id': timetable.id,
            'timetable_name': timetable.name,
            'entry_count': len(entries),
            'entries': serializer.data,
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': f'Generation error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# UNIT ENDPOINTS  (global catalogue — units are shared across courses)
# ============================================================================

def _unit_to_dict(unit, include_courses=False):
    d = {
        'id': unit.id,
        'code': unit.code,
        'name': unit.name,
        'description': unit.description,
        'credits': unit.credits,
        'hours_per_week': unit.hours_per_week,
        'created_at': unit.created_at.isoformat(),
        'updated_at': unit.updated_at.isoformat(),
    }
    if include_courses:
        d['courses'] = [
            {'id': cu.course_id, 'code': cu.course.code, 'name': cu.course.name,
             'year_of_study': cu.year_of_study, 'semester': cu.semester, 'is_core': cu.is_core}
            for cu in unit.course_links.select_related('course')
        ]
    return d


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_units(request):
    """List all units or create a new unit."""
    try:
        if request.method == 'GET':
            q = request.query_params.get('q', '')
            qs = Unit.objects.all()
            if q:
                qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
            serializer = UnitSerializer(qs, many=True)
            return Response(serializer.data)

        # POST — create a new global unit
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            unit = serializer.save()
            return Response(UnitSerializer(unit).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        print(f"ERROR in list_create_units: {e}")
        traceback.print_exc()
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_unit(request, pk):
    """Retrieve, update, or delete a unit."""
    try:
        unit = get_object_or_404(Unit, pk=pk)

        if request.method == 'GET':
            return Response(_unit_to_dict(unit, include_courses=True))

        if request.method == 'PUT':
            serializer = UnitSerializer(unit, data=request.data, partial=True)
            if serializer.is_valid():
                unit = serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # DELETE
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        import traceback
        print(f"ERROR in retrieve_update_delete_unit: {e}")
        traceback.print_exc()
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# COURSE → UNITS  (list, link, unlink)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_units(request, pk):
    """List all units linked to a course."""
    try:
        course = get_object_or_404(Course, pk=pk)
        links  = CourseUnit.objects.filter(course=course).select_related('unit')
        data = [
            {
                'unit_id':       cu.unit.id,
                'code':          cu.unit.code,
                'name':          cu.unit.name,
                'credits':       cu.unit.credits,
                'hours_per_week':cu.unit.hours_per_week,
                'year_of_study': cu.year_of_study,
                'semester':      cu.semester,
                'is_core':       cu.is_core,
                'link_id':       cu.id,
            }
            for cu in links
        ]
        return Response(data)
    except Exception as e:
        import traceback
        print(f"ERROR in course_units: {e}")
        traceback.print_exc()
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_unit_to_course(request, course_pk, unit_pk):
    """Link an existing unit to a course."""
    try:
        course = get_object_or_404(Course, pk=course_pk)
        unit   = get_object_or_404(Unit,   pk=unit_pk)
        data   = request.data

        cu, created = CourseUnit.objects.get_or_create(
            unit=unit, course=course,
            defaults={
                'year_of_study': int(data.get('year_of_study', 1)),
                'semester':      int(data.get('semester', 1)),
                'is_core':       bool(data.get('is_core', True)),
            }
        )
        if not created:
            return Response({'detail': 'Unit is already linked to this course.'}, status=status.HTTP_200_OK)

        return Response({
            'detail': f'Unit {unit.code} linked to course {course.code}.',
            'link_id': cu.id,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        import traceback
        print(f"ERROR in link_unit_to_course: {e}")
        traceback.print_exc()
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unlink_unit_from_course(request, course_pk, unit_pk):
    """Unlink a unit from a course (does NOT delete the unit itself)."""
    course = get_object_or_404(Course, pk=course_pk)
    unit   = get_object_or_404(Unit,   pk=unit_pk)
    deleted, _ = CourseUnit.objects.filter(unit=unit, course=course).delete()
    if deleted:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({'detail': 'Link not found.'}, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# HIERARCHY CONVENIENCE ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hierarchy_overview(request):
    """Return full School → Department → Course tree (no units for perf)."""
    data = []
    for school in School.objects.prefetch_related('departments__programs__courses'):
        school_entry = {
            'id': school.id, 'name': school.name, 'code': school.code,
            'departments': []
        }
        for dept in school.departments.all():
            dept_entry = {
                'id': dept.id, 'name': dept.name, 'code': dept.code,
                'courses': []
            }
            courses = Course.objects.filter(
                Q(department=dept) | Q(program__department=dept)
            ).distinct().values('id', 'code', 'name', 'semester', 'credits')
            dept_entry['courses'] = list(courses)
            school_entry['departments'].append(dept_entry)
        data.append(school_entry)
    return Response(data)
