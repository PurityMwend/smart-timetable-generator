"""
App-level URL routing – registers DRF router for all viewsets.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'lecturers', views.LecturerViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'timeslots', views.TimeSlotViewSet)
router.register(r'lecturer-availability', views.LecturerAvailabilityViewSet)
router.register(r'timetable-entries', views.TimetableEntryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload-data/', views.upload_data, name='upload_data'),
    path('courses/<int:course_id>/timetable/', views.course_timetable, name='course_timetable'),
    path('lecturers/<int:lecturer_id>/timetable/', views.lecturer_timetable, name='lecturer_timetable'),
    path('rooms/<int:room_id>/timetable/', views.room_timetable, name='room_timetable'),
]
