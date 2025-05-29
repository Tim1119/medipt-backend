from rest_framework import serializers
from .models import PatientMedicalRecord 

class PatientRepresentationMixin:
    """
    Mixin to add common user-related fields to patient serializers.
    """
    def add_user_fields_to_representation(self, instance, representation):
        representation['email'] = instance.user.email
        representation['role'] = instance.user.role
        representation['active'] = instance.user.is_active
        representation['verified'] = instance.user.is_verified
        return representation

    def add_medical_record_to_representation(self, instance, representation):
        from .serializers import PatientMedicalRecordSerializer
        try:
            medical_record = instance.patientmedicalrecord
            representation['medical_record'] = PatientMedicalRecordSerializer(medical_record).data
        except PatientMedicalRecord.DoesNotExist:
            representation['medical_record'] = {}
        return representation