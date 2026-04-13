"""
URL routing for timetable API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'schools', api_views.SchoolViewSet)
router.register(r'departments', api_views.DepartmentViewSet)
router.register(r'courses', api_views.CourseViewSet)
router.register(r'lecturers', api_views.LecturerViewSet)
router.register(r'rooms', api_views.RoomViewSet)
router.register(r'timeslots', api_views.TimeSlotViewSet)
router.register(r'lecturer-availability', api_views.LecturerAvailabilityViewSet)
router.register(r'timetable-entries', api_views.TimetableEntryViewSet)

urlpatterns = [
    # Authentication & CSRF
    path('auth/csrf-token/', api_views.get_csrf_token, name='get_csrf_token'),
    path('auth/register/', api_views.register_user, name='register'),
    path('auth/login/', api_views.login_user, name='login'),
    path('auth/logout/', api_views.logout_user, name='logout'),
    path('auth/current-user/', api_views.current_user, name='current_user'),
    path('auth/profile/', api_views.update_user_profile, name='update_profile'),
    
    # CRUD endpoints
    path('', include(router.urls)),
    
    # Data operations
    path('upload/', api_views.upload_data, name='upload_data'),
    path('upload/training-data/', api_views.upload_training_data, name='upload_training_data'),
    path('upload/data/', api_views.upload_data_file, name='upload_data_file'),
    path('template/', api_views.download_excel_template, name='download_template'),
    
    # Timetable operations
    path('generate/', api_views.generate_timetable, name='generate_timetable'),
    path('export-pdf/', api_views.export_timetable_pdf, name='export_timetable_pdf'),
    
    # Filtered views
    path('courses/<int:course_id>/timetable/', api_views.course_timetable, name='course_timetable'),
    path('lecturers/<int:lecturer_id>/timetable/', api_views.lecturer_timetable, name='lecturer_timetable'),
    path('rooms/<int:room_id>/timetable/', api_views.room_timetable, name='room_timetable'),
    
    # Training Data (Admin only)
    path('training-data/', api_views.training_data_list, name='training_data_list'),
    path('training-data/<int:pk>/', api_views.training_data_detail, name='training_data_detail'),
    path('common-units/', api_views.common_units_list, name='common_units_list'),
    path('common-units/<int:pk>/', api_views.common_unit_detail, name='common_unit_detail'),
    path('recurrent-units/', api_views.recurrent_units_list, name='recurrent_units_list'),
    path('recurrent-units/<int:pk>/', api_views.recurrent_unit_detail, name='recurrent_unit_detail'),
]
