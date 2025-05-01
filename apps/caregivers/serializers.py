from .models import Caregiver
from rest_framework import serializers


class CaregiverSerializer(serializers.ModelSerializer):
    active = serializers.BooleanField(source='user.is_active', read_only=True)
    verified = serializers.BooleanField(source='user.is_verified', read_only=True)

    class Meta:
        model = Caregiver
        fields = ['first_name','last_name','caregiver_type','date_of_birth','marital_status','profile_picture','gender',
                  'phone_number','address','slug','id','active','verified','created_at','updated_at','staff_number']


class BasicCaregiverSerializer(CaregiverSerializer):
    '''This serializer is used to create a health record (vital sign/diagnosis) the view uses it to send list of serializers'''
    caregiver_name = serializers.CharField(source='full_name_with_role', read_only=True)
    class Meta:
        model = Caregiver
        fields = ['id','caregiver_name']
