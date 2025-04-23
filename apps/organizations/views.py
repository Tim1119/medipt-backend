from django.shortcuts import get_object_or_404
from django.db.models import Count, Q,Sum
from apps.patients.serializers import PatientDiagnosisDetailsSerializer, PatientSerializer,CreatePatientDiagnosisWithVitalSignSerializer
from apps.patients.models import Patient, PatientDiagnosisDetails
from rest_framework.generics import ListAPIView,CreateAPIView,UpdateAPIView,RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from apps.caregivers.serializers import CaregiverSerializer,BasicCaregiverSerializer
from apps.patients.exceptions import PatientNotFoundException
from apps.organizations.utils import StandardResultsSetPagination
from .models import Organization
from .permissions import IsOrganization,IsOrganizationAndOwnsObject
from apps.caregivers.models import Caregiver
from django_filters.rest_framework import DjangoFilterBackend
from apps.accounts.user_roles import UserRoles
from shared.validators import validate_uuid
from rest_framework.exceptions import ValidationError
from .exceptions import PatientNotificationFailedException
import uuid
from rest_framework.exceptions import NotFound
from django.db.models import Prefetch
from .serializers import OrganizationRegisterPatientSerializer, OrganizationBasicInfoSerializer
from .tasks import send_patient_account_creation_notification_email
from apps.caregivers.exceptions import CaregiverNotFoundException
from apps.caregivers.permissions import IsCaregiver
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView


class OrganizationDashboardView(APIView):
    """
    Retrieves organization statistics and latest 10 caregivers and patient for the dashboard.
    """
    permission_classes = [IsAuthenticated, IsOrganization]

    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, "organization") or request.user.organization is None:
            raise NotFound("Organization not found for user.")

        organization = request.user.organization

        caregiver_stats = Caregiver.objects.filter(organization=organization).aggregate(
            total=Count("pkid"),
            active=Count("pkid", filter=Q(user__is_active=True)),
            verified=Count("pkid", filter=Q(user__is_verified=True)),
        )

        patient_stats = Patient.objects.filter(organization=organization).aggregate(
            total=Count("pkid"),
            active=Count("pkid", filter=Q(user__is_active=True)),
            verified=Count("pkid", filter=Q(user__is_verified=True)),
            active_male=Count("pkid", filter=Q(user__is_active=True, gender="Male")),
            active_female=Count("pkid", filter=Q(user__is_active=True, gender="Female")),
            verified_male=Count("pkid", filter=Q(user__is_verified=True, gender="Male")),
            verified_female=Count("pkid", filter=Q(user__is_verified=True, gender="Female")),
        )

        latest_caregivers = Caregiver.objects.filter(organization=organization,user__is_active=True,user__is_verified=True)[:10]
        latest_patients = Patient.objects.filter(organization=organization,user__is_active=True,user__is_verified=True)[:10]

        response_data = {
            "statistics": {
                "caregivers": caregiver_stats,
                "patients": patient_stats,
            },
            "latest_caregivers": CaregiverSerializer(latest_caregivers, many=True).data,
            "latest_patients": PatientSerializer(latest_patients, many=True).data,
        }

        return Response({"message": "Organization Dashboard Data", "data": response_data}, status=status.HTTP_200_OK)


class OrganizationLatestCaregiversListView(ListAPIView):
    """
    Lists top 10 latest caregivers associated with the authenticated organization based on filter criteria.
    """
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = CaregiverSerializer

    def get_queryset(self):
        if self.request.user.organization is None:
            raise NotFound("Organization not found for user.")
        return Caregiver.objects.filter(organization=self.request.user.organization,user__is_active=True,user__is_verified=True)[:10]
    


class OrganizationCaregiversListView(ListAPIView):
    """
    Lists caregivers associated with the authenticated organization based on filter criteria.
    """
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = CaregiverSerializer
    # pagination_class = StandardResultsSetPagination
    # filter_backends = [SearchFilter]
    # search_fields = ['first_name', 'last_name', 'staff_number', 'caregiver_type']

    def get_queryset(self):
        if self.request.user.organization is None:
            raise NotFound("Organization not found for user.")
        return Caregiver.objects.filter(organization=self.request.user.organization,user__is_active=True,user__is_verified=True)



class OrganizationLatestPatientListView(ListAPIView):
    """
    Returns a list of top 10 patients associated with the authenticated organization the can  be filtered for active,verified or invited
    """ 
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = PatientSerializer
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'medical_id']

    def get_queryset(self):
        if self.request.user.organization is None:
            raise NotFound("Organization not found for user.")
        return Patient.objects.filter(organization=self.request.user.organization  ,user__is_active=True,user__is_verified=True)[:10]
    

class OrganizationPatientListView(ListAPIView):
    """
    Returns a list of  patients associated with the authenticated organization the can  be filtered for active,verified or invited
    """ 
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = PatientSerializer
    # pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.organization is None:
            raise NotFound("Organization not found for user.")
        return Patient.objects.filter(organization=self.request.user.organization,user__is_active=True,user__is_verified=True)
    

class OrganizationCreatePatientView(CreateAPIView):

    """
    Creates a new patient associated with the authenticated organization and send a notification
    to the user notifying them that an account has been created for them
    """ 

    serializer_class = OrganizationRegisterPatientSerializer
    permission_classes = [IsAuthenticated,IsOrganization]

    def perform_create(self, serializer):
        with transaction.atomic():
            patient = serializer.save()  
            try:
                send_patient_account_creation_notification_email.delay(
                    patient_email=serializer.validated_data['email'],
                    patient_password=serializer.validated_data['password'],
                    patient_full_name =serializer.validated_data['first_name']+serializer.validated_data['last_name'],
                    organization_name=self.request.user.organization.name
                )

            except Exception as e:
                raise PatientNotificationFailedException(f"Patient created but failed to send notification: {str(e)}")
            
class OrganizationBasicInfoView(RetrieveUpdateAPIView):
    """
    Updates an organization basic details (profile): first name, last name, email, phone number, and address.
    """
    serializer_class = OrganizationBasicInfoSerializer
    permission_classes = [IsAuthenticated,IsOrganizationAndOwnsObject]
    lookup_field='id'

    def get_object(self):
        id = self.kwargs.get('id')

        if not validate_uuid(id):
            raise ValidationError(f"Invalid Organization ID: {id}")

        return get_object_or_404(Organization, id=id, user=self.request.user)

class OrganizationToggleCaregiverStatusView(UpdateAPIView):
    """
    Helps to Toggle the status of the caregiver from active to non-active and vice versa
    """ 
    model = Caregiver
    serializer_class = CaregiverSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    lookup_field='id'

    def get_object(self):
        caregiver_id = self.kwargs['id']
        if not validate_uuid(caregiver_id):
            # raise ValidationError(f"Invalid Caregiver Id {pk}")
            raise ValidationError(f"Caregiver details not found")
        caregiver = Caregiver.objects.filter(id=caregiver_id, organization=self.request.user.organization).first()
        if not caregiver:
            raise CaregiverNotFoundException()
        return caregiver
    
    def update(self, request, *args, **kwargs):
        caregiver = self.get_object()
        caregiver.user.is_active = not caregiver.user.is_active
        caregiver.user.save() 
        serializer = CaregiverSerializer(caregiver,many=False)
        return Response({ "message": "Caregiver status toggled successfully", "data": serializer.data},status=status.HTTP_200_OK)
    
class OrganizationTogglePatientStatusView(UpdateAPIView):
    """
    Helps to Toggle the status of the patient from active to non-active and vice versa
    """ 
    model = Patient
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    lookup_field='id'

    def get_object(self):
        patient_id = self.kwargs['id']
        if not validate_uuid(patient_id):
            raise ValidationError(f"Patient details not found")
        patient = Patient.objects.filter(id=patient_id, organization=self.request.user.organization).first()
        if not patient:
            raise PatientNotFoundException()
        return patient
    
    def update(self, request, *args, **kwargs):
        patient = self.get_object()
        patient.user.is_active = not patient.user.is_active
        patient.user.save() 
        serializer = PatientSerializer(patient,many=False)
        return Response({ "message": "Patient status toggled successfully", "data": serializer.data},status=status.HTTP_200_OK)
    

class OrganizationBasicCaregiversInfoListView(ListAPIView):

    """
    Retrieve all caregivers and basic information about them for an organization.
    """
    
    serializer_class = BasicCaregiverSerializer
    permission_classes = [IsAuthenticated,IsOrganization]

    def get_queryset(self):
        organization = self.request.user.organization
        return Caregiver.objects.filter(organization=organization)
    
    
class OrganizationHealthRecordHistory(ListAPIView):
    """
    View to retrieve only patients who have diagnosis records.
    """
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = PatientDiagnosisDetailsSerializer

    def get_queryset(self):
        return (
            PatientDiagnosisDetails.objects
            .select_related('patient', 'organization', 'caregiver')  # Optimized queries
            .filter(diagnoses__isnull=False)  # Ensures only patients with diagnosis records are included
            .distinct()
        )
