from django.urls import path,include
from .views import InviteCaregiverView,CaregiverAcceptInvitationView

urlpatterns = [
    path('invite-caregiver/', InviteCaregiverView.as_view(), name='invite-caregiver'),
    path("caregivers/invite/accept/<uuid:token>/",CaregiverAcceptInvitationView.as_view(),name="caregiver_accept_invitation",),   
]

