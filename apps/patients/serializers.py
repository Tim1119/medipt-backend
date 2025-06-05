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
            return instance



class DiagnosisSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient Diagnoses only. It is used in GroupedDiagnosisDetailsForPatientSerializer for grouping.
    It is not used in isolation  and does not contain detils, like caregiver, patient and organization unlike PatientDiagnosisDetailsSerializer
    """
    class Meta:
        model = PatientDiagnosisDetails
        fields = ['id', 'assessment', 'diagnoses', 'medication', 'health_allergies', 'health_care_center', 'notes', 'created_at']




from rest_framework import serializers
from .models import Patient, PatientDiagnosisDetails
# from .serializers import PatientDiagnosisDetailsSerializer

# class PatientDiagnosisSerializer(serializers.ModelSerializer):
#     """
#     A serializer that combines patient information with grouped diagnoses.
#     Can also provide detailed diagnosis records when requested.
#     """
#     diagnoses = serializers.SerializerMethodField()
#     patient_profile_picture = serializers.SerializerMethodField()
#     patient_name = serializers.CharField(source='full_name', read_only=True)

#     class Meta:
#         model = Patient
#         fields = ['id', 'patient_name', 'medical_id', 'diagnoses', 'patient_profile_picture', 'address']

#     def get_diagnoses(self, obj):
#         """
#         Get diagnosis details for a specific patient.
#         Returns detailed diagnoses if 'detailed' is True in context, otherwise grouped.
#         """
#         detailed = self.context.get('detailed', False)
#         if hasattr(obj, 'patientdiagnosisdetails_set'):
#             diagnoses = obj.patientdiagnosisdetails_set.all()
#         else:
#             diagnoses = PatientDiagnosisDetails.objects.filter(patient=obj)

#         # if detailed:
#             # Return detailed diagnosis records
#         return DiagnosisSerializer(diagnoses, many=True, context=self.context).data
#         # else:
#         #     # Return grouped diagnosis data (e.g., just the diagnosis names)
#         #     return [diagnosis.diagnoses for diagnosis in diagnoses]

#     def get_patient_profile_picture(self, obj):
#         """
#         Get the patient's profile picture URL.
#         """
#         if obj.profile_picture:
#             request = self.context.get('request')
#             relative_url = obj.profile_picture.url
#             if request:
#                 return request.build_absolute_uri(relative_url)
#             return relative_url
#         return None



class PatientDiagnosisSerializer(serializers.ModelSerializer):
    """
    A serializer that combines patient information with diagnoses.
    Handles three different views based on context:
    - 'latest': Shows only the latest diagnosis (for list page)
    - 'all': Shows all diagnoses (for history page) 
    - 'single': Shows single diagnosis (handled by separate serializer)
    """
    diagnoses = serializers.SerializerMethodField()
    patient_profile_picture = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source='full_name', read_only=True)
    diagnosis_count = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'patient_name', 'medical_id', 'diagnoses', 'patient_profile_picture', 'address', 'diagnosis_count']

    def get_diagnoses(self, obj):
        """
        Get diagnosis details for a specific patient based on view type.
        """
        view_type = self.context.get('view_type', 'all')
        
        if hasattr(obj, 'patientdiagnosisdetails_set'):
            diagnoses = obj.patientdiagnosisdetails_set.all()
        else:
            diagnoses = PatientDiagnosisDetails.objects.filter(patient=obj).order_by('-created_at')

        if view_type == 'latest':
            # Return only the latest diagnosis for list page
            latest_diagnosis = diagnoses.first()
            if latest_diagnosis:
                return DiagnosisSerializer([latest_diagnosis], many=True, context=self.context).data
            return []
        else:
            # Return all diagnoses for history page
            return DiagnosisSerializer(diagnoses, many=True, context=self.context).data

    def get_diagnosis_count(self, obj):
        """
        Get total count of diagnoses for this patient.
        Useful for showing "X diagnoses" in the UI.
        """
        if hasattr(obj, 'patientdiagnosisdetails_set'):
            return obj.patientdiagnosisdetails_set.count()
        return PatientDiagnosisDetails.objects.filter(patient=obj).count()

    def get_patient_profile_picture(self, obj):
        """
        Get the patient's profile picture URL.
        """
        if obj.profile_picture:
            request = self.context.get('request')
            relative_url = obj.profile_picture.url
            if request:
                return request.build_absolute_uri(relative_url)
            return relative_url
        return None


class SingleDiagnosisSerializer(serializers.ModelSerializer):
    """
    Serializer for single diagnosis detail view.
    Includes patient info and detailed diagnosis information.
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_medical_id = serializers.CharField(source='patient.medical_id', read_only=True)
    patient_profile_picture = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    caregiver_name = serializers.CharField(source='caregiver.full_name_with_role', read_only=True)
    caregiver_id = serializers.CharField(source='caregiver.id', read_only=True)
    vital_signs = serializers.SerializerMethodField()

    class Meta:
        model = PatientDiagnosisDetails
        fields = [
            'id',
            'patient_name',
            'patient_medical_id', 
            'patient_profile_picture',
            'organization_name',
            'caregiver_name',
            'caregiver_id',
            'assessment',
            'diagnoses',
            'medication',
            'health_allergies',
            'health_care_center',
            'notes',
            'vital_signs',
            'created_at',
            'updated_at'
        ]

    def get_patient_profile_picture(self, obj):
        """
        Get the patient's profile picture URL.
        """
        if obj.patient.profile_picture:
            request = self.context.get('request')
            relative_url = obj.patient.profile_picture.url
            if request:
                return request.build_absolute_uri(relative_url)
            return relative_url
        return None

    def get_vital_signs(self, obj):
        """
        Get vital signs associated with this diagnosis.
        """
        try:
            vital_signs = obj.vitalsign
            return {
                'body_temperature': vital_signs.body_temperature,
                'pulse_rate': vital_signs.pulse_rate,
                'blood_pressure': vital_signs.blood_pressure,
                'blood_oxygen': vital_signs.blood_oxygen,
                'respiration_rate': vital_signs.respiration_rate,
                'weight': vital_signs.weight
            }
        except VitalSign.DoesNotExist:
            return None

class VitalSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSign
        fields = ['body_temperature', 'pulse_rate', 'blood_pressure', 'blood_oxygen', 'respiration_rate']


class PatientDiagnosisWithVitalSignSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    caregiver = serializers.PrimaryKeyRelatedField(read_only=True)
    vital_sign = VitalSignSerializer(write_only=True, required=False)  # Optional for updates

    # Response fields
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
        if obj.patient.profile_picture:
            request = self.context.get('request')
            relative_url = obj.patient.profile_picture.url
            if request:
                return request.build_absolute_uri(relative_url)
            return relative_url
        return None

    def create(self, validated_data):
        vital_sign_data = validated_data.pop('vital_sign', None)
        try:
            with transaction.atomic():
                patient_diagnosis = PatientDiagnosisDetails.objects.create(**validated_data)
                if vital_sign_data:
                    vital_sign_serializer = VitalSignSerializer(data=vital_sign_data)
                    vital_sign_serializer.is_valid(raise_exception=True)
                    VitalSign.objects.create(
                        patient_diagnoses_details=patient_diagnosis, 
                        **vital_sign_serializer.validated_data
                    )
            return patient_diagnosis
        except IntegrityError as e:
            raise ValidationError(f"Database error: {str(e)}")

    def update(self, instance, validated_data):
        vital_sign_data = validated_data.pop('vital_sign', None)
        try:
            with transaction.atomic():
                # Update PatientDiagnosisDetails instance
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()

                # Update or create VitalSign instance
                if vital_sign_data:
                    vital_sign_serializer = VitalSignSerializer(data=vital_sign_data)
                    vital_sign_serializer.is_valid(raise_exception=True)
                    VitalSign.objects.update_or_create(
                        patient_diagnoses_details=instance,
                        defaults=vital_sign_serializer.validated_data
                    )
            return instance
        except IntegrityError as e:
            raise ValidationError(f"Database error: {str(e)}")


class PatientBasicInfoSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='full_name', read_only=True)
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id',
            'patient_name',
            'medical_id',
            'profile_picture',
        ]

    def get_profile_picture(self, obj):
        return obj.profile_picture_url