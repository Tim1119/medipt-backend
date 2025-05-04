from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CaregiverViewSet, LatestCaregiversView,ToggleCaregiverStatusView


router = DefaultRouter()
router.register('all-caregivers', CaregiverViewSet, basename='caregiver')


urlpatterns = [
    path('', include(router.urls)),
    path('latest-caregivers/', LatestCaregiversView.as_view(),name='latest-caregivers'),
    path('toggle-caregiver-status/<str:slug>/', ToggleCaregiverStatusView.as_view(),name='toggle-caregiver-status'),
]


