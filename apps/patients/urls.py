from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from .views import (PatientUpdateRegistrationDetailsView,UpdatePatientBasicInfoView,PatientDetailByMedicalIDView,PatientDiagnosisDetailsRecordsView
#                     ,PatientDiagnosisListView,CreatePatientDiagnosisWithVitalSignView,OrganizationUpdatePatientRegistrationDetailsView)
from .views import (LatestPatientsView,PatientViewSet,TogglePatientStatusView,RegisterPatientView,PatientRegistrationDetailsByMedicalIDView,
PatientDiagnosisListView,PatientDiagnosisHistoryView,SingleDiagnosisDetailView,CreatePatientDiagnosisWithVitalSignView,UpdatePatientDiagnosisWithVitalSignView,PatientBasicInfoView)
# PatientDiagnosisView)

router = DefaultRouter()
router.register('all-patients',PatientViewSet, basename='patient')



urlpatterns = [
   path('', include(router.urls)),
   path('latest-patients/', LatestPatientsView.as_view(),name='latest-patients'),
   path('toggle-patient-status/<str:slug>/', TogglePatientStatusView.as_view(),name='toggle-patient-status'),
   path('register-new-patient/', RegisterPatientView.as_view(), name='register-new-patient'),
   path('patient-registration-details-by-medical-id/<str:medical_id>/', PatientRegistrationDetailsByMedicalIDView.as_view(), name='register-new-patient'),
   path('patients-diagnoses/', PatientDiagnosisListView.as_view(), name='patient-diagnosis-list'),
   path('patient-diagnoses-history/<str:medical_id>/', PatientDiagnosisHistoryView.as_view(), name='patient-diagnosis-history'),
   path('patient-diagnoses-detail/<uuid:id>/', SingleDiagnosisDetailView.as_view(), name='diagnosis-detail'),
   path('create-patient-health-record/<str:patient_id>/',CreatePatientDiagnosisWithVitalSignView.as_view(),name='create-patient-health-record'),
   path('update-patient-health-record/<str:id>/',UpdatePatientDiagnosisWithVitalSignView.as_view(),name='update-patient-health-record'),
   path('patient-basic-info/<str:id>/',PatientBasicInfoView.as_view(),name='patient-basic-info'),

   
]


