from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CaregiverViewSet, LatestCaregiversView,ToggleCaregiverStatusView,OrganizationAllCaregiversBasicInfoView


router = DefaultRouter()
router.register('all-caregivers', CaregiverViewSet, basename='caregiver')


urlpatterns = [
    path('', include(router.urls)),
    path('latest-caregivers/', LatestCaregiversView.as_view(),name='latest-caregivers'),
    path('toggle-caregiver-status/<str:slug>/', ToggleCaregiverStatusView.as_view(),name='toggle-caregiver-status'),
    path('all-caregivers-in-organization/', OrganizationAllCaregiversBasicInfoView.as_view(),name='all-caregivers-in-organization'),
]


