from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from .views import (PatientUpdateRegistrationDetailsView,UpdatePatientBasicInfoView,PatientDetailByMedicalIDView,PatientDiagnosisDetailsRecordsView
#                     ,PatientDiagnosisListView,CreatePatientDiagnosisWithVitalSignView,OrganizationUpdatePatientRegistrationDetailsView)
from .views import (LatestPatientsView,PatientViewSet,TogglePatientStatusView,RegisterPatientView,PatientRegistrationDetailsByMedicalIDView)

router = DefaultRouter()
router.register('all-patients',PatientViewSet, basename='patient')



urlpatterns = [
   path('', include(router.urls)),
   path('latest-patients/', LatestPatientsView.as_view(),name='latest-patients'),
   path('toggle-patient-status/<str:slug>/', TogglePatientStatusView.as_view(),name='toggle-patient-status'),
    path('register-new-patient/', RegisterPatientView.as_view(), name='register-new-patient'),
    path('patient-registration-details-by-medical-id/<str:medical_id>/', PatientRegistrationDetailsByMedicalIDView.as_view(), name='register-new-patient'),
   # path('update-patient-registration-details/<uuid:id>/',PatientUpdateRegistrationDetailsView.as_view(),name='update-patient-registration-details'),
   # path('update-patient-registration-details/<str:medical_id>/',OrganizationUpdatePatientRegistrationDetailsView.as_view(),name='update-patient-registration-details'),
   # path('update-patient-basic_info/<uuid:id>/',UpdatePatientBasicInfoView.as_view(),name='update-patient-basic-info'),
   # # path('patient-detail-view/<uuid:id>/',PatientDetailView.as_view(),name='patient-detail-view'),
   # path('patient-details-by-medical-id/<str:medical_id>/',PatientDetailByMedicalIDView.as_view(),name='patient-details-by-medical-id'),
   # path('patient-diagnosis-detail-record/<uuid:patient_diagnosis_details_id>/',PatientDiagnosisDetailsRecordsView.as_view(),name='patient-diagnosis-detail-record'),
   # # path('patient-diagnosis-records/', PatientDiagnosisListView.as_view(), name='patient-diagnosis-records'),
   # path('patient-diagnosis-records/<str:medical_id>/', PatientDiagnosisListView.as_view(), name='patient-diagnosis-records-with-id'),
   # path("create-diagnoses-with-vital-sign/<uuid:patient_id>/",  CreatePatientDiagnosisWithVitalSignView.as_view(), name="create_patient_diagnosis"),
   
]


