from django.urls import path,include
from .views import (LatestCaregiverView)


urlpatterns = [
   path('latest-caregivers/', LatestCaregiverView.as_view(),name='latest-caregivers'),
]


