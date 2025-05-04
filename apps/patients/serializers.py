from .models import Patient,PatientMedicalRecord,PatientDiagnosisDetails
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VitalSign
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth.password_validation import validate_password
import logging

logger = logging.getLogger(__name__)



User = get_user_model()

class PatientMedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientMedicalRecord
        fields = ['blood_group', 'genotype', 'weight', 'height', 'allergies']



class PatientDetailSerializer(serializers.ModelSerializer):
    """This serializer is used to get detailed information about a patient"""
    
    # email = serializers.SerializerMethodField()
    medical_record = PatientMedicalRecordSerializer(source='patientmedicalrecord', read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 'marital_status', 
            'profile_picture', 'gender', 'phone_number', 'emergency_phone_number', 'medical_id',
            'address', 'medical_record'
        ]
        read_only_fields = ['id', 'medical_id']
    
    # def get_email(self, obj):
    #     """Get the email from the related User model"""
    #     return obj.user.email
    
    def to_representation(self, instance):
        """
        Custom representation to include medical record data if it exists
        """
        representation = super().to_representation(instance)
        try:
            medical_record = instance.patientmedicalrecord
            medical_record_data = PatientMedicalRecordSerializer(medical_record).data
            representation.update(medical_record_data)
        except PatientMedicalRecord.DoesNotExist:
            pass
        return representation



class OrganizationUpdatePatientRegistrationDetailsSerializer(serializers.ModelSerializer):
    """This serializer is used by the organization to update a patient's information"""
    
    medical_record = PatientMedicalRecordSerializer(required=False)
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'marital_status', 
            'profile_picture', 'gender', 'phone_number', 'emergency_phone_number',
            'address', 'medical_record'
        ]
    
    # def validate_email(self, value):
    #     """ Ensure the email is unique and case-insensitive if it's being changed """
    #     patient = self.instance
    #     current_email = patient.user.email
        
    #     if value.lower() != current_email.lower():
    #         if not User.objects.filter(email__iexact=value).exists():
    #             raise serializers.ValidationError("An account with this email does not already exists.")
    #     return value.lower()
    
    def update(self, instance, validated_data):
        try:
            # Handle medical record update if provided
            if 'medical_record' in validated_data:
                medical_record_data = validated_data.pop('medical_record')
                medical_record, created = PatientMedicalRecord.objects.get_or_create(patient=instance)
                for attr, value in medical_record_data.items():
                    setattr(medical_record, attr, value)
                medical_record.save()
            
            
            # Update patient information
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            return instance
            
        except IntegrityError:
            raise serializers.ValidationError("Database error occurred while updating the patient.")
        except Exception as e:
            logger.error(f"Unexpected error updating patient {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"An error occurred while updating the patient: {str(e)}")
    
    def to_representation(self, instance):
        """
        Custom representation to include medical record data
        """
        representation = super().to_representation(instance)
        try:
            medical_record = instance.patientmedicalrecord
            medical_record_data = PatientMedicalRecordSerializer(medical_record).data
            representation.update(medical_record_data)
        except PatientMedicalRecord.DoesNotExist:
            pass
        
        # Add email from the User model
        representation['email'] = instance.user.email
        
        return representation



class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        exclude=['user']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['role'] = instance.user.role 
        representation['active'] = instance.user.is_active
        representation['verified'] = instance.user.is_verified
        return representation


class UpdatePatientRegistrationDetailsSerializer(serializers.ModelSerializer):
    medical_record = PatientMedicalRecordSerializer(required=False)  # Nested serializer
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id',
            
            'first_name',
            'last_name'
            'medical_id',
            'date_of_birth',
            'marital_status',
            'profile_picture',
            'gender',
            'phone_number',
            'emergency_phone_number',
            'address',
            'medical_record',  # Handle medical record updates properly
        ]
        read_only_fields = ['id', 'medical_id']

    def update(self, instance, validated_data):
        medical_record_data = validated_data.pop('medical_record', None)

        # Update Patient fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle nested medical record update
        if medical_record_data:
            medical_record, created = PatientMedicalRecord.objects.get_or_create(patient=instance)
            for attr, value in medical_record_data.items():
                setattr(medical_record, attr, value)
            medical_record.save()

        return instance



class UpdatePatientBasicInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name','email', 'phone_number', 'address']

    def validate_email(self, value):
        """Ensure email is not already used by another user"""
        if User.objects.filter(email=value).exclude(id=self.instance.user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def update(self, instance, validated_data):
        """Ensure email update applies to the associated user model"""
        user = instance.user
        if 'email' in validated_data:
            user.email = validated_data['email']
            user.save()  

        return super().update(instance, validated_data)



class PatientDiagnosisDetailsSerializer(serializers.ModelSerializer):
    """
    This serializer is used to serialize patient diagnoses (not grouped).
    It is used to get the diagnosis for a particular ailment or health condition.
    """
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    caregiver_name = serializers.CharField(source='caregiver.full_name_with_role', read_only=True)
    patient_medical_id = serializers.CharField(source='patient.medical_id', read_only=True)
    patient_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = PatientDiagnosisDetails
        fields = ['id','patient_profile_picture','patient_name','patient_medical_id','organization_name','caregiver_name','assessment','health_care_center','diagnoses','medication','slug','notes','created_at','health_allergies']
        

    def get_patient_profile_picture(self, obj):
        if obj.patient.profile_picture:
            request = self.context.get('request')
            relative_url = obj.patient.profile_picture.url 
            if request:
                return request.build_absolute_uri(relative_url)  
            return relative_url 
        return None
    

class PatientDiagnosisSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient Diagnoses only. It is used in GroupedDiagnosisDetailsForPatientSerializer for grouping.
    It is not used in isolation  and does not contain detils, like caregiver, patient and organization unlike PatientDiagnosisDetailsSerializer
    """
    class Meta:
        model = PatientDiagnosisDetails
        fields = [
            'id', 
            'assessment', 
            'diagnoses', 
            'medication', 
            'health_allergies', 
            'health_care_center', 
            'notes', 
            'created_at'
        ]



class PatientDiagnosisListSerializer(serializers.ModelSerializer):
    "This serializer is used to group diagnoses for each patient unlike the PatientDiagnosisDetailsSerializer that is not grouped"
    diagnoses = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'medical_id', 
            'diagnoses',
            'profile_picture',
            'address',
        ]
    

    def get_diagnoses(self, obj):
        """
        Get diagnosis details for a specific patient.
        Uses prefetched data if available, otherwise queries.
        """
        if hasattr(obj, 'patientdiagnosisdetails_set'):
            diagnoses = obj.patientdiagnosisdetails_set.all()
        else:
            diagnoses = PatientDiagnosisDetails.objects.filter(patient=obj)

        return PatientDiagnosisSerializer(diagnoses, many=True).data
    



class VitalSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSign
        fields = ['body_temperature', 'pulse_rate', 'blood_pressure', 'blood_oxygen', 'respiration_rate','weight']

class CreatePatientDiagnosisWithVitalSignSerializer(serializers.ModelSerializer):
    """Serializer for creating patient diagnosis with vital signs."""

    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    caregiver = serializers.UUIDField(write_only=True)
    vital_sign = VitalSignSerializer(write_only=True)

    # Custom fields for response
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_profile_picture = serializers.SerializerMethodField()
    patient_medical_id = serializers.CharField(source='patient.medical_id', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    caregiver_name = serializers.CharField(source='caregiver.name', read_only=True)
    slug = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PatientDiagnosisDetails
        fields = [
            'id', 'patient', 'organization', 'caregiver', 'assessment', 'health_care_center', 
            'diagnoses', 'medication', 'notes', 'health_allergies', 'vital_sign', 'patient_name',
            'patient_profile_picture', 'patient_medical_id', 'organization_name', 'caregiver_name',
            'slug', 'created_at'
        ]

    def get_patient_profile_picture(self, obj):
        """Retrieve the full URL of the patient profile picture."""
        if obj.patient.profile_picture:
            request = self.context.get('request')
            relative_url = obj.patient.profile_picture.url  # e.g., "/media/default.png"
            return request.build_absolute_uri(relative_url) if request else relative_url
        return None
    
    def create(self, validated_data):
        """Create patient diagnosis and associated vital sign in a transaction."""
        vital_sign_data = validated_data.pop('vital_sign')

        with transaction.atomic():
            patient_diagnosis = PatientDiagnosisDetails.objects.create(**validated_data)
            VitalSign.objects.create(patient_diagnoses_details=patient_diagnosis, **vital_sign_data)
        
        return patient_diagnosis
    
class PatientBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'profile_picture','medical_id']


# class PatientDiagnosisWithVitalSignSerializer(serializers.ModelSerializer):
#     """Serializer for patient diagnosis with vital signs CRUD operations."""

#     patient = serializers.PrimaryKeyRelatedField(read_only=True)
#     organization = serializers.PrimaryKeyRelatedField(read_only=True)
#     caregiver = serializers.UUIDField(write_only=True, required=False)  # Made optional for updates
#     vital_sign = VitalSignSerializer(required=False)  # Made optional for partial updates

#     # Custom fields for response
#     patient_name = serializers.CharField(source='patient.full_name', read_only=True)
#     patient_profile_picture = serializers.SerializerMethodField()
#     patient_medical_id = serializers.CharField(source='patient.medical_id', read_only=True)
#     organization_name = serializers.CharField(source='organization.name', read_only=True)
#     caregiver_name = serializers.CharField(source='caregiver.name', read_only=True)
#     slug = serializers.CharField(read_only=True)
#     created_at = serializers.DateTimeField(read_only=True)
    
#     # Add related vital sign data for retrieval operations
#     vital_sign_data = serializers.SerializerMethodField(read_only=True)

#     class Meta:
#         model = PatientDiagnosisDetails
#         fields = [
#             'id', 'patient', 'organization', 'caregiver', 'assessment', 'health_care_center', 
#             'diagnoses', 'medication', 'notes', 'health_allergies', 'vital_sign', 'vital_sign_data',
#             'patient_name', 'patient_profile_picture', 'patient_medical_id', 'organization_name', 
#             'caregiver_name', 'slug', 'created_at'
#         ]

#     def get_patient_profile_picture(self, obj):
#         """Retrieve the full URL of the patient profile picture."""
#         if obj.patient.profile_picture:
#             request = self.context.get('request')
#             relative_url = obj.patient.profile_picture.url
#             return request.build_absolute_uri(relative_url) if request else relative_url
#         return None
    
#     def get_vital_sign_data(self, obj):
#         """Get the associated vital sign data."""
#         try:
#             vital_sign = VitalSign.objects.get(patient_diagnoses_details=obj)
#             return VitalSignSerializer(vital_sign).data
#         except VitalSign.DoesNotExist:
#             return None
    
#     def create(self, validated_data):
#         """Create patient diagnosis and associated vital sign in a transaction."""
#         vital_sign_data = validated_data.pop('vital_sign', None)

#         with transaction.atomic():
#             patient_diagnosis = PatientDiagnosisDetails.objects.create(**validated_data)
#             if vital_sign_data:
#                 VitalSign.objects.create(patient_diagnoses_details=patient_diagnosis, **vital_sign_data)
        
#         return patient_diagnosis
    
#     def update(self, instance, validated_data):
#         """Update patient diagnosis and associated vital sign in a transaction."""
#         vital_sign_data = validated_data.pop('vital_sign', None)
        
#         with transaction.atomic():
#             # Update the diagnosis instance
#             for attr, value in validated_data.items():
#                 setattr(instance, attr, value)
#             instance.save()
            
#             # Update vital signs if provided
#             if vital_sign_data:
#                 vital_sign, created = VitalSign.objects.get_or_create(
#                     patient_diagnoses_details=instance,
#                     defaults=vital_sign_data
#                 )
#                 if not created:
#                     for attr, value in vital_sign_data.items():
#                         setattr(vital_sign, attr, value)
#                     vital_sign.save()
                    
#         return instance