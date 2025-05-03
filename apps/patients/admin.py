from django.contrib import admin
from .models import Patient,PatientMedicalRecord,PatientDiagnosisDetails,VitalSign

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'medical_id', 'date_of_birth', 'organization','id')
    search_fields = ('first_name', 'last_name', 'medical_id')
    list_filter = ('organization', 'gender', 'marital_status')

@admin.register(PatientDiagnosisDetails)
class PatientDiagnosisDetailsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'organization', 'caregiver', 'assessment', 'created_at','id')
    search_fields = ('patient__first_name', 'patient__last_name', 'organization__name')
    list_filter = ('organization', 'caregiver')

@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ('patient_diagnoses_details', 'body_temperature', 'pulse_rate', 'blood_pressure', 'blood_oxygen', 'respiration_rate','id')  # Updated field name
    search_fields = ('patient_diagnoses_details__patient__first_name', 'patient_diagnoses_details__patient__last_name')  # Updated field name
    list_filter = ('patient_diagnoses_details__organization',)  

@admin.register(PatientMedicalRecord)
class PatientMedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'blood_group', 'genotype', 'weight', 'height','id')
    search_fields = ('patient__first_name', 'patient__last_name')
