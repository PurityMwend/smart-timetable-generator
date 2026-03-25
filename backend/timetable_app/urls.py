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
]
