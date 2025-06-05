from django.urls import path,include
# from .views import (OrganizationDashboardView, OrganizationHealthRecordHistory,OrganizationLatestCaregiversListView,OrganizationCaregiversListView,OrganizationLatestPatientListView,OrganizationPatientListView,OrganizationCreatePatientView,OrganizationBasicInfoView,
#                     OrganizationToggleCaregiverStatusView,OrganizationBasicCaregiversInfoListView,OrganizationTogglePatientStatusView)
from .views import (OrganizationDashboardView,OrganizationProfileView)


urlpatterns = [
   path('organization-statistics/',OrganizationDashboardView.as_view(),name='organization-statistics'),
   path('profile/', OrganizationProfileView.as_view(), name='organization_profile'),
   # path('organization-latest-caregivers-list/',OrganizationLatestCaregiversListView.as_view(),name='organization-latest-caregivers-list'),
   # path('organization-all-caregivers-list/',OrganizationCaregiversListView.as_view(),name='organization-all-caregivers-list'),
   # path('organization-latest-patients-list/',OrganizationLatestPatientListView.as_view(),name='organization-latest-patients-list'),
   # path('organization-all-patients-list/',OrganizationPatientListView.as_view(),name='organization-all-patients-list'),
   # path('organization-create-patient/',OrganizationCreatePatientView.as_view(),name='organization-create-patient'),
   # path('organization-basic-info/<str:id>/',OrganizationBasicInfoView.as_view(),name='organization-basic-info'),
   # path('organization-toggle-cargiver-status/<uuid:id>/',OrganizationToggleCaregiverStatusView.as_view(),name='organization-toggle-caregiver-status'),
   # path('organization-toggle-patient-status/<uuid:id>/',OrganizationTogglePatientStatusView.as_view(),name='organization-toggle-patient-status'),
   # path('organization-caregivers-basic-info-list/',OrganizationBasicCaregiversInfoListView.as_view(),name='organization-caregivers-basic-info-list'),
   # path('organization-health-record-history/',OrganizationHealthRecordHistory.as_view(),name='organization-health-record-history'),
]


