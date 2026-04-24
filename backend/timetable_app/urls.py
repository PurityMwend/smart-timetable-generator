"""
URL routing for timetable_app API endpoints.
Comprehensive REST API routes for all resources.
"""
from django.urls import path
from . import api_views

app_name = 'timetable_app'

urlpatterns = [
    # =====================================================================
    # AUTH ENDPOINTS
    # =====================================================================
    path('auth/register/', api_views.register_user, name='register'),
    path('auth/login/', api_views.login_user, name='login'),
    path('auth/logout/', api_views.logout_user, name='logout'),
    path('auth/me/', api_views.get_current_user, name='current_user'),
    path('auth/current-user/', api_views.get_current_user, name='current_user_alias'),
    path('auth/change-password/', api_views.change_password, name='change_password'),
    path('auth/csrf-token/', api_views.get_csrf_token, name='csrf_token'),
    
    # =====================================================================
    # SCHOOL ENDPOINTS
    # =====================================================================
    path('schools/', api_views.list_create_schools, name='school_list_create'),
    path('schools/<int:pk>/', api_views.retrieve_update_delete_school, name='school_detail'),
    path('schools/<int:pk>/departments/', api_views.school_departments, name='school_departments'),
    
    # =====================================================================
    # DEPARTMENT ENDPOINTS
    # =====================================================================
    path('departments/', api_views.list_create_departments, name='department_list_create'),
    path('departments/<int:pk>/', api_views.retrieve_update_delete_department, name='department_detail'),
    path('departments/<int:pk>/courses/', api_views.department_courses, name='department_courses'),
    
    # =====================================================================
    # PROGRAM ENDPOINTS
    # =====================================================================
    path('programs/', api_views.list_create_programs, name='program_list_create'),
    path('programs/<int:pk>/', api_views.retrieve_update_delete_program, name='program_detail'),
    
    # =====================================================================
    # COURSE ENDPOINTS
    # =====================================================================
    path('courses/', api_views.list_create_courses, name='course_list_create'),
    path('courses/<int:pk>/', api_views.retrieve_update_delete_course, name='course_detail'),
    path('courses/<int:pk>/lecturers/', api_views.course_lecturers, name='course_lecturers'),
    path('courses/<int:pk>/timetable/', api_views.course_timetable, name='course_timetable'),
    
    # =====================================================================
    # LECTURER ENDPOINTS
    # =====================================================================
    path('lecturers/', api_views.list_create_lecturers, name='lecturer_list_create'),
    path('lecturers/<int:pk>/', api_views.retrieve_update_delete_lecturer, name='lecturer_detail'),
    path('lecturers/<int:pk>/timetable/', api_views.lecturer_timetable, name='lecturer_timetable'),
    path('lecturers/<int:pk>/availability/', api_views.lecturer_availability, name='lecturer_availability'),
    
    # =====================================================================
    # ROOM ENDPOINTS
    # =====================================================================
    path('rooms/', api_views.list_create_rooms, name='room_list_create'),
    path('rooms/<int:pk>/', api_views.retrieve_update_delete_room, name='room_detail'),
    path('rooms/<int:pk>/availability/', api_views.room_availability, name='room_availability'),
    
    # =====================================================================
    # STUDENT CLASS ENDPOINTS
    # =====================================================================
    path('classes/', api_views.list_create_student_classes, name='class_list_create'),
    path('classes/<int:pk>/', api_views.retrieve_update_delete_student_class, name='class_detail'),
    path('classes/<int:pk>/timetable/', api_views.student_class_timetable, name='class_timetable'),
    path('classes/<int:pk>/enrollments/', api_views.student_class_enrollments, name='class_enrollments'),
    
    # =====================================================================
    # TIME SLOT ENDPOINTS
    # =====================================================================
    path('time-slots/', api_views.list_create_time_slots, name='time_slot_list_create'),
    path('time-slots/<int:pk>/', api_views.retrieve_update_delete_time_slot, name='time_slot_detail'),
    
    # =====================================================================
    # TIMETABLE ENTRY ENDPOINTS
    # =====================================================================
    path('timetable-entries/', api_views.list_create_timetable_entries, name='timetable_entry_list_create'),
    path('timetable-entries/<int:pk>/', api_views.retrieve_update_delete_timetable_entry, name='timetable_entry_detail'),
    
    # =====================================================================
    # TIMETABLE ENDPOINTS
    # =====================================================================
    path('timetables/', api_views.list_create_timetables, name='timetable_list_create'),
    path('timetables/<int:pk>/', api_views.retrieve_update_delete_timetable, name='timetable_detail'),
    path('timetables/<int:pk>/generate/', api_views.generate_timetable, name='timetable_generate'),
    path('timetables/<int:pk>/export/', api_views.export_timetable, name='timetable_export'),
    path('timetables/import/', api_views.import_timetable, name='timetable_import'),

    # =====================================================================
    # UPLOAD & QUICK-GENERATE ENDPOINTS
    # =====================================================================
    path('upload-sample-data/', api_views.upload_sample_data, name='upload_sample_data'),
    path('generate-timetable/', api_views.generate_timetable_quick, name='generate_timetable_quick'),
    path('sample-template/', api_views.download_sample_template, name='sample_template'),

    # =====================================================================
    # UNIT ENDPOINTS  (global unit catalogue)
    # =====================================================================
    path('units/', api_views.list_create_units, name='unit_list_create'),
    path('units/<int:pk>/', api_views.retrieve_update_delete_unit, name='unit_detail'),

    # =====================================================================
    # COURSE → UNIT LINK / UNLINK
    # =====================================================================
    path('courses/<int:pk>/units/', api_views.course_units, name='course_units'),
    path('courses/<int:course_pk>/units/<int:unit_pk>/', api_views.link_unit_to_course, name='link_unit'),
    path('courses/<int:course_pk>/units/<int:unit_pk>/unlink/', api_views.unlink_unit_from_course, name='unlink_unit'),

    # =====================================================================
    # HIERARCHY CONVENIENCE
    # =====================================================================
    path('hierarchy/', api_views.hierarchy_overview, name='hierarchy_overview'),
]
