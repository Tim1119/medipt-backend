from rest_framework import serializers
from apps.accounts.models import User
from django.contrib.auth.password_validation import validate_password
from apps.patients.models import Patient
from apps.patients.serializers import PatientMedicalRecordSerializer
from django.db import IntegrityError, transaction
from apps.accounts.user_roles import UserRoles
from apps.patients.models import PatientMedicalRecord
from .models import Organization



class OrganizationRegisterPatientSerializer(serializers.ModelSerializer):

    '''This serializer is used by the organziation to signup a patient'''

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, validators=[validate_password])
    medical_record = PatientMedicalRecordSerializer(write_only=True)
    medical_id = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'first_name','last_name','email', 'password', 'date_of_birth', 'marital_status', 
            'profile_picture', 'gender', 'phone_number', 'emergency_phone_number','medical_id',
            'address','medical_record'
        ]
        read_only_fields = ['id','medical_id']

    
    def validate_email(self, value):
        """ Ensure the email is unique and case-insensitive """
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower() 


    def create(self, validated_data):
        try:

            medical_record_data = validated_data.pop('medical_record')

            # Extract user data
            user_data = {
                'email': validated_data.pop('email'),
                'password': validated_data.pop('password'),
                'role':UserRoles.PATIENT,
                'is_active':True,
                'is_verified':True,
            }

            with transaction.atomic():
                # Create user
                user = User.objects.create_user(**user_data)

                # Create patient
                patient = Patient.objects.create(user=user,organization=self.context['request'].user.organization, **validated_data)

                # Create patient medical record
                PatientMedicalRecord.objects.create(patient=patient, **medical_record_data)

            return patient

        except IntegrityError:
            raise serializers.ValidationError("Database error occurred while creating the patient.")
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred while creating the patient: {str(e)}")


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
    
class OrganizationBasicInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False,source='user.email') 

    class Meta:
        model = Organization
        # fields = ['name', 'acronym', 'phone_number', 'address', 'email']
        #  client should not be able to change their acronym as it used to generate medical id
        fields = ['name', 'phone_number', 'address', 'email'] 

    def validate_email(self, value):
        """Ensure email is not already used by another user"""
        user = getattr(self.instance, "user", None)
        if user and User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def update(self, instance, validated_data):
        # Extract nested user data if present
        user_data = validated_data.pop('user', {})

        # Update the nested User instance if email is provided
        email = user_data.get('email')
        if email:
            instance.user.email = email
            instance.user.save(update_fields=["email"])

        # For the rest of the organization fields, update using the parent's update method
        return super().update(instance, validated_data)
