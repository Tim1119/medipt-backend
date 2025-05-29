from .models import Patient,PatientMedicalRecord,PatientDiagnosisDetails
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VitalSign
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email as django_validate_email
from apps.accounts.user_roles import UserRoles
from .exceptions import PatientNotificationFailedException
import logging
from .tasks import send_patient_account_creation_notification_email
from .mixins import PatientRepresentationMixin
from django.core.validators import RegexValidator


logger = logging.getLogger(__name__)



User = get_user_model()


class PatientSerializer(PatientRepresentationMixin,serializers.ModelSerializer):

    class Meta:
        model = Patient
        exclude=['user']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return self.add_user_fields_to_representation(instance, representation)

class PatientMedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientMedicalRecord
        fields = ['blood_group', 'genotype', 'weight', 'height', 'allergies']


class BasePatientSerializer(serializers.ModelSerializer):
    medical_record = PatientMedicalRecordSerializer(required=False)

    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'medical_id', 'date_of_birth', 'marital_status',
            'profile_picture', 'gender', 'phone_number', 'emergency_phone_number', 'address',
            'medical_record'
        ]
        read_only_fields = ['id', 'medical_id']

    def validate_profile_picture(self, value):
        if value:
            if value.size > 2 * 1024 * 1024:  # 2MB limit
                raise serializers.ValidationError("Profile picture must be under 2MB.")
            if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("Profile picture must be a JPG or PNG file.")
        return value

    def validate_phone_number(self, value):
        if value:
            validator = RegexValidator(
                r'^\+?1?\d{9,15}$',
                message="Phone number must be a valid format (e.g., +1234567890)."
            )
            validator(value)
        return value

    def validate_first_name(self, value):
        if value:
            validator = RegexValidator(
                r'^[a-zA-Z\s-]+$',
                message="First name can only contain letters, spaces, or hyphens."
            )
            validator(value)
        return value

    def validate_last_name(self, value):
        if value:
            validator = RegexValidator(
                r'^[a-zA-Z\s-]+$',
                message="Last name can only contain letters, spaces, or hyphens."
            )
            validator(value)
        return value

class OrganizationRegisterPatientSerializer(PatientRepresentationMixin,BasePatientSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, validators=[validate_password])

    class Meta(BasePatientSerializer.Meta):
        fields = BasePatientSerializer.Meta.fields + ['email', 'password']

    def validate_email(self, value):
        django_validate_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        medical_record_data = validated_data.pop('medical_record', {})
        user_data = {
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'role': UserRoles.PATIENT,
            'is_active': True,
            'is_verified': True,
        }

        with transaction.atomic():
            user = User.objects.create_user(**user_data)
            patient = Patient.objects.create(
                user=user,
                organization=self.context['request'].user.organization,
                **validated_data
            )
            PatientMedicalRecord.objects.create(patient=patient, **medical_record_data)

            try:
                # Send password reset link instead of plain password
                send_patient_account_creation_notification_email.delay(
                    patient_email=user.email,
                    patient_full_name=f"{patient.first_name} {patient.last_name}",
                    organization_name=self.context['request'].user.organization.name,
                    patient_id=str(patient.id)  # For generating reset link
                )
            except Exception as e:
                raise PatientNotificationFailedException(f"Patient created but failed to send notification: {str(e)}")

        return patient

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation = self.add_user_fields_to_representation(instance, representation)
        representation = self.add_medical_record_to_representation(instance, representation)
        return representation


class PatientDetailSerializer(PatientRepresentationMixin, BasePatientSerializer):
    # medical_record = PatientMedicalRecordSerializer(source='patientmedicalrecord', read_only=True)
    medical_record = PatientMedicalRecordSerializer(required=False, partial=True)
    # email = serializers.EmailField(source='user.email', read_only=True)  # Display email but don't allow updates

    class Meta(BasePatientSerializer.Meta):
        # fields = BasePatientSerializer.Meta.fields + ['medical_record', 'email', 'role', 'active', 'verified']
        fields = BasePatientSerializer.Meta.fields + ['medical_record']
        # read_only_fields = ['id', 'medical_id', 'email', 'role', 'active', 'verified', 'pkid', 'created_at', 'updated_at', 'organization', 'slug']
        read_only_fields = ['id', 'medical_id']


    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation = self.add_user_fields_to_representation(instance, representation)
        representation = self.add_medical_record_to_representation(instance, representation)
        return representation
    
    def update(self, instance, validated_data):
        """
        Update patient instance and related medical record.
        """
        medical_record_data = validated_data.pop('medical_record', None)
        
        with transaction.atomic():
            # Update patient fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update medical record if provided
            if medical_record_data:
                try:
                    medical_record = instance.patientmedicalrecord
                    for attr, value in medical_record_data.items():
                        setattr(medical_record, attr, value)
                    medical_record.save()
                except PatientMedicalRecord.DoesNotExist:
                    # Create medical record if it doesn't exist
                    PatientMedicalRecord.objects.create(
                        patient=instance,
                        **medical_record_data
                    )
            
            logger.info(f"Updated patient {instance.medical_id} and medical record")
            return instance
# class PatientDetailSerializer(serializers.ModelSerializer):
#     """This serializer is used to get detailed information about a patient"""
    
#     # email = serializers.SerializerMethodField()
#     medical_record = PatientMedicalRecordSerializer(source='patientmedicalrecord', read_only=True)
    
#     class Meta:
#         model = Patient
#         fields = [
#             'id', 'first_name', 'last_name', 'date_of_birth', 'marital_status', 
#             'profile_picture', 'gender', 'phone_number', 'emergency_phone_number', 'medical_id',
#             'address', 'medical_record'
#         ]
#         read_only_fields = ['id', 'medical_id']
    
#     # def get_email(self, obj):
#     #     """Get the email from the related User model"""
#     #     return obj.user.email
    
#     def to_representation(self, instance):
#         """
#         Custom representation to include medical record data if it exists
#         """
#         representation = super().to_representation(instance)
#         try:
#             medical_record = instance.patientmedicalrecord
#             medical_record_data = PatientMedicalRecordSerializer(medical_record).data
#             representation.update(medical_record_data)
#         except PatientMedicalRecord.DoesNotExist:
#             pass
#         return representation



# class OrganizationUpdatePatientRegistrationDetailsSerializer(serializers.ModelSerializer):
#     """This serializer is used by the organization to update a patient's information"""
    
#     medical_record = PatientMedicalRecordSerializer(required=False)
    
#     class Meta:
#         model = Patient
#         fields = [
#             'first_name', 'last_name', 'date_of_birth', 'marital_status', 
#             'profile_picture', 'gender', 'phone_number', 'emergency_phone_number',
#             'address', 'medical_record'
#         ]
    
#     # def validate_email(self, value):
#     #     """ Ensure the email is unique and case-insensitive if it's being changed """
#     #     patient = self.instance
#     #     current_email = patient.user.email
        
#     #     if value.lower() != current_email.lower():
#     #         if not User.objects.filter(email__iexact=value).exists():
#     #             raise serializers.ValidationError("An account with this email does not already exists.")
#     #     return value.lower()
    
#     def update(self, instance, validated_data):
#         try:
#             # Handle medical record update if provided
#             if 'medical_record' in validated_data:
#                 medical_record_data = validated_data.pop('medical_record')
#                 medical_record, created = PatientMedicalRecord.objects.get_or_create(patient=instance)
#                 for attr, value in medical_record_data.items():
#                     setattr(medical_record, attr, value)
#                 medical_record.save()
            
            
#             # Update patient information
#             for attr, value in validated_data.items():
#                 setattr(instance, attr, value)
#             instance.save()
            
#             return instance
            
#         except IntegrityError:
#             raise serializers.ValidationError("Database error occurred while updating the patient.")
#         except Exception as e:
#             logger.error(f"Unexpected error updating patient {instance.id}: {str(e)}")
#             raise serializers.ValidationError(f"An error occurred while updating the patient: {str(e)}")
    
#     def to_representation(self, instance):
#         """
#         Custom representation to include medical record data
#         """
#         representation = super().to_representation(instance)
#         try:
#             medical_record = instance.patientmedicalrecord
#             medical_record_data = PatientMedicalRecordSerializer(medical_record).data
#             representation.update(medical_record_data)
#         except PatientMedicalRecord.DoesNotExist:
#             pass
        
#         # Add email from the User model
#         representation['email'] = instance.user.email
        
#         return representation




# class UpdatePatientRegistrationDetailsSerializer(serializers.ModelSerializer):
#     medical_record = PatientMedicalRecordSerializer(required=False)  # Nested serializer
#     email = serializers.EmailField(read_only=True)

#     class Meta:
#         model = Patient
#         fields = [
#             'id',
            
#             'first_name',
#             'last_name'
#             'medical_id',
#             'date_of_birth',
#             'marital_status',
#             'profile_picture',
#             'gender',
#             'phone_number',
#             'emergency_phone_number',
#             'address',
#             'medical_record',  # Handle medical record updates properly
#         ]
#         read_only_fields = ['id', 'medical_id']

#     def update(self, instance, validated_data):
#         medical_record_data = validated_data.pop('medical_record', None)

#         # Update Patient fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Handle nested medical record update
#         if medical_record_data:
#             medical_record, created = PatientMedicalRecord.objects.get_or_create(patient=instance)
#             for attr, value in medical_record_data.items():
#                 setattr(medical_record, attr, value)
#             medical_record.save()

#         return instance



# class UpdatePatientBasicInfoSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(write_only=True)
#     class Meta:
#         model = Patient
#         fields = ['first_name', 'last_name','email', 'phone_number', 'address']

#     def validate_email(self, value):
#         """Ensure email is not already used by another user"""
#         if User.objects.filter(email=value).exclude(id=self.instance.user.id).exists():
#             raise serializers.ValidationError("This email is already in use.")
#         return value

#     def update(self, instance, validated_data):
#         """Ensure email update applies to the associated user model"""
#         user = instance.user
#         if 'email' in validated_data:
#             user.email = validated_data['email']
#             user.save()  

#         return super().update(instance, validated_data)



# class PatientDiagnosisDetailsSerializer(serializers.ModelSerializer):
#     """
#     This serializer is used to serialize patient diagnoses (not grouped).
#     It is used to get the diagnosis for a particular ailment or health condition.
#     """
#     organization_name = serializers.CharField(source='organization.name', read_only=True)
#     patient_name = serializers.CharField(source='patient.full_name', read_only=True)
#     caregiver_name = serializers.CharField(source='caregiver.full_name_with_role', read_only=True)
#     patient_medical_id = serializers.CharField(source='patient.medical_id', read_only=True)
#     patient_profile_picture = serializers.SerializerMethodField()

#     class Meta:
#         model = PatientDiagnosisDetails
#         fields = ['id','patient_profile_picture','patient_name','patient_medical_id','organization_name','caregiver_name','assessment','health_care_center','diagnoses','medication','slug','notes','created_at','health_allergies']
        

#     def get_patient_profile_picture(self, obj):
#         if obj.patient.profile_picture:
#             request = self.context.get('request')
#             relative_url = obj.patient.profile_picture.url 
#             if request:
#                 return request.build_absolute_uri(relative_url)  
#             return relative_url 
#         return None
    

# class PatientDiagnosisSerializer(serializers.ModelSerializer):
#     """
#     Serializer for Patient Diagnoses only. It is used in GroupedDiagnosisDetailsForPatientSerializer for grouping.
#     It is not used in isolation  and does not contain detils, like caregiver, patient and organization unlike PatientDiagnosisDetailsSerializer
#     """
#     class Meta:
#         model = PatientDiagnosisDetails
#         fields = [
#             'id', 
#             'assessment', 
#             'diagnoses', 
#             'medication', 
#             'health_allergies', 
#             'health_care_center', 
#             'notes', 
#             'created_at'
#         ]



# class PatientDiagnosisListSerializer(serializers.ModelSerializer):
#     "This serializer is used to group diagnoses for each patient unlike the PatientDiagnosisDetailsSerializer that is not grouped"
#     diagnoses = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Patient
#         fields = [
#             'id', 
#             'first_name', 
#             'last_name', 
#             'medical_id', 
#             'diagnoses',
#             'profile_picture',
#             'address',
#         ]
    

#     def get_diagnoses(self, obj):
#         """
#         Get diagnosis details for a specific patient.
#         Uses prefetched data if available, otherwise queries.
#         """
#         if hasattr(obj, 'patientdiagnosisdetails_set'):
#             diagnoses = obj.patientdiagnosisdetails_set.all()
#         else:
#             diagnoses = PatientDiagnosisDetails.objects.filter(patient=obj)

#         return PatientDiagnosisSerializer(diagnoses, many=True).data
    



# class VitalSignSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VitalSign
#         fields = ['body_temperature', 'pulse_rate', 'blood_pressure', 'blood_oxygen', 'respiration_rate','weight']

# class CreatePatientDiagnosisWithVitalSignSerializer(serializers.ModelSerializer):
#     """Serializer for creating patient diagnosis with vital signs."""

#     patient = serializers.PrimaryKeyRelatedField(read_only=True)
#     organization = serializers.PrimaryKeyRelatedField(read_only=True)
#     caregiver = serializers.UUIDField(write_only=True)
#     vital_sign = VitalSignSerializer(write_only=True)

#     # Custom fields for response
#     patient_name = serializers.CharField(source='patient.full_name', read_only=True)
#     patient_profile_picture = serializers.SerializerMethodField()
#     patient_medical_id = serializers.CharField(source='patient.medical_id', read_only=True)
#     organization_name = serializers.CharField(source='organization.name', read_only=True)
#     caregiver_name = serializers.CharField(source='caregiver.name', read_only=True)
#     slug = serializers.CharField(read_only=True)
#     created_at = serializers.DateTimeField(read_only=True)

#     class Meta:
#         model = PatientDiagnosisDetails
#         fields = [
#             'id', 'patient', 'organization', 'caregiver', 'assessment', 'health_care_center', 
#             'diagnoses', 'medication', 'notes', 'health_allergies', 'vital_sign', 'patient_name',
#             'patient_profile_picture', 'patient_medical_id', 'organization_name', 'caregiver_name',
#             'slug', 'created_at'
#         ]

#     def get_patient_profile_picture(self, obj):
#         """Retrieve the full URL of the patient profile picture."""
#         if obj.patient.profile_picture:
#             request = self.context.get('request')
#             relative_url = obj.patient.profile_picture.url  # e.g., "/media/default.png"
#             return request.build_absolute_uri(relative_url) if request else relative_url
#         return None
    
#     def create(self, validated_data):
#         """Create patient diagnosis and associated vital sign in a transaction."""
#         vital_sign_data = validated_data.pop('vital_sign')

#         with transaction.atomic():
#             patient_diagnosis = PatientDiagnosisDetails.objects.create(**validated_data)
#             VitalSign.objects.create(patient_diagnoses_details=patient_diagnosis, **vital_sign_data)
        
#         return patient_diagnosis
    
# class PatientBasicInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Patient
#         fields = ['first_name', 'last_name', 'profile_picture','medical_id']


# # class PatientDiagnosisWithVitalSignSerializer(serializers.ModelSerializer):
# #     """Serializer for patient diagnosis with vital signs CRUD operations."""

# #     patient = serializers.PrimaryKeyRelatedField(read_only=True)
# #     organization = serializers.PrimaryKeyRelatedField(read_only=True)
# #     caregiver = serializers.UUIDField(write_only=True, required=False)  # Made optional for updates
# #     vital_sign = VitalSignSerializer(required=False)  # Made optional for partial updates

# #     # Custom fields for response
# #     patient_name = serializers.CharField(source='patient.full_name', read_only=True)
# #     patient_profile_picture = serializers.SerializerMethodField()
# #     patient_medical_id = serializers.CharField(source='patient.medical_id', read_only=True)
# #     organization_name = serializers.CharField(source='organization.name', read_only=True)
# #     caregiver_name = serializers.CharField(source='caregiver.name', read_only=True)
# #     slug = serializers.CharField(read_only=True)
# #     created_at = serializers.DateTimeField(read_only=True)
    
# #     # Add related vital sign data for retrieval operations
# #     vital_sign_data = serializers.SerializerMethodField(read_only=True)

# #     class Meta:
# #         model = PatientDiagnosisDetails
# #         fields = [
# #             'id', 'patient', 'organization', 'caregiver', 'assessment', 'health_care_center', 
# #             'diagnoses', 'medication', 'notes', 'health_allergies', 'vital_sign', 'vital_sign_data',
# #             'patient_name', 'patient_profile_picture', 'patient_medical_id', 'organization_name', 
# #             'caregiver_name', 'slug', 'created_at'
# #         ]

# #     def get_patient_profile_picture(self, obj):
# #         """Retrieve the full URL of the patient profile picture."""
# #         if obj.patient.profile_picture:
# #             request = self.context.get('request')
# #             relative_url = obj.patient.profile_picture.url
# #             return request.build_absolute_uri(relative_url) if request else relative_url
# #         return None
    
# #     def get_vital_sign_data(self, obj):
# #         """Get the associated vital sign data."""
# #         try:
# #             vital_sign = VitalSign.objects.get(patient_diagnoses_details=obj)
# #             return VitalSignSerializer(vital_sign).data
# #         except VitalSign.DoesNotExist:
# #             return None
    
# #     def create(self, validated_data):
# #         """Create patient diagnosis and associated vital sign in a transaction."""
# #         vital_sign_data = validated_data.pop('vital_sign', None)

# #         with transaction.atomic():
# #             patient_diagnosis = PatientDiagnosisDetails.objects.create(**validated_data)
# #             if vital_sign_data:
# #                 VitalSign.objects.create(patient_diagnoses_details=patient_diagnosis, **vital_sign_data)
        
# #         return patient_diagnosis
    
# #     def update(self, instance, validated_data):
# #         """Update patient diagnosis and associated vital sign in a transaction."""
# #         vital_sign_data = validated_data.pop('vital_sign', None)
        
# #         with transaction.atomic():
# #             # Update the diagnosis instance
# #             for attr, value in validated_data.items():
# #                 setattr(instance, attr, value)
# #             instance.save()
            
# #             # Update vital signs if provided
# #             if vital_sign_data:
# #                 vital_sign, created = VitalSign.objects.get_or_create(
# #                     patient_diagnoses_details=instance,
# #                     defaults=vital_sign_data
# #                 )
# #                 if not created:
# #                     for attr, value in vital_sign_data.items():
# #                         setattr(vital_sign, attr, value)
# #                     vital_sign.save()
                    
# #         return instance