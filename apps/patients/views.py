from django.shortcuts import render,get_object_or_404
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from .serializers import OrganizationRegisterPatientSerializer,PatientDetailSerializer,PatientSerializer,DiagnosisSerializer,PatientDiagnosisWithVitalSignSerializer,PatientBasicInfoSerializer
# from .serializers import PatientBasicInfoSerializer, PatientDetailSerializer, UpdatePatientRegistrationDetailsSerializer,UpdatePatientBasicInfoSerializer,PatientSerializer,PatientDiagnosisDetailsSerializer,PatientDiagnosisListSerializer,CreatePatientDiagnosisWithVitalSignSerializer,OrganizationUpdatePatientRegistrationDetailsSerializer
from .models import Patient, PatientDiagnosisDetails
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import UpdateAPIView,RetrieveAPIView,ListAPIView,CreateAPIView
from .exceptions import PatientNotFoundException,PatientMedicalIDNotFoundException
from shared.validators import validate_uuid
from rest_framework.exceptions import ValidationError
from .permissions import IsAllowedToUpdatePatientRegistrationDetails,IsPatient
from apps.accounts.user_roles import UserRoles
from rest_framework.exceptions import PermissionDenied,NotFound
from apps.organizations.permissions import IsOrganization
from apps.caregivers.permissions import IsCaregiver
from django.db.models import Prefetch   
from apps.caregivers.models import Caregiver
from rest_framework.response import Response
from rest_framework import status
from apps.caregivers.exceptions import CaregiverNotFoundException
from django.db import transaction
from rest_framework.mixins import RetrieveModelMixin,UpdateModelMixin,DestroyModelMixin,ListModelMixin
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from shared.pagination import StandardResultsSetPagination
from rest_framework import generics




# Create your views here.
class LatestPatientsView(ListAPIView):
    """
      Returns a list of top 5 latest patients associated with the organization or logged in caregiver organization.
    """
    # permission_classes = [IsAuthenticated, IsOrganizationOrCaregiver]
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = PatientSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == UserRoles.ORGANIZATION:
            organization = user.organization
        elif user.role == UserRoles.CAREGIVER:
            organization = user.caregiver.organization
        else:
            raise NotFound("Organization not found for user.")

        if organization is None:
            raise NotFound("Organization not found for user.")

        return Patient.objects.filter(organization=organization,user__is_verified=True,user__is_active=True,user__role=UserRoles.PATIENT)[:5]

class PatientViewSet(ListModelMixin,RetrieveModelMixin,UpdateModelMixin,DestroyModelMixin,viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['first_name', 'last_name', 'medical_id']
    filterset_fields = ['medical_id', 'user__is_active']
    pagination_class = StandardResultsSetPagination
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user

        if user.role == UserRoles.ORGANIZATION:
            organization = user.organization
        elif user.role == UserRoles.CAREGIVER:
            organization = user.caregiver.organization

        else:
            raise NotFound("Organization not found for user.")

        if organization is None:
            raise NotFound("Organization not found for user.")

        return Patient.objects.filter(organization=organization,user__is_verified=True,user__is_active=True,user__role=UserRoles.PATIENT)

class TogglePatientStatusView(UpdateAPIView):
    """
    Helps to Toggle the status of the patient from active to non-active and vice versa
    """ 
    model = Patient
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    lookup_field='slug'

    def get_object(self):
        patient_slug = self.kwargs['slug']
        patient = Patient.objects.filter(slug=patient_slug, organization=self.request.user.organization).first()
        if not patient:
            raise PatientNotFoundException()
        return patient
    
    def update(self, request, *args, **kwargs):
        patient = self.get_object()
        patient.user.is_active = not patient.user.is_active
        patient.user.save() 
        serializer = PatientSerializer(patient,many=False)
        return Response({ "message": "Patient status toggled successfully", "data": serializer.data},status=status.HTTP_200_OK)

class RegisterPatientView(CreateAPIView):

    """
    Creates a new patient associated with the authenticated organization and send a notification
    to the user notifying them that an account has been created for them
    """ 

    serializer_class = OrganizationRegisterPatientSerializer
    permission_classes = [IsAuthenticated, IsOrganization]

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save()

class PatientRegistrationDetailsByMedicalIDView(generics.RetrieveUpdateAPIView):
    """
    Retrieve detailed information for a specific patient by medical_id.
    Accessible to authenticated organization or caregiver users.
    Returns patient details including medical record and user-related fields.
    """
    serializer_class = PatientDetailSerializer
    permission_classes = [IsAuthenticated, IsOrganization | IsCaregiver]
    lookup_field = 'medical_id'

    def get_queryset(self):
        """
        Filter patients to only those belonging to the organization of the authenticated user or caregiver.
        """
        user = self.request.user
        if user.role == UserRoles.ORGANIZATION:
            organization = user.organization
        elif user.role == UserRoles.CAREGIVER:
            organization = user.caregiver.organization
        else:
            raise PermissionDenied("You do not have permission to access this resource.")
        if organization is None:
            raise NotFound("Organization not found for user.")
        return Patient.objects.filter(organization=organization).select_related('user').prefetch_related('patientmedicalrecord')

    def get_object(self):
        """
        Retrieve a patient by medical_id with custom error handling.
        """
        medical_id = self.kwargs[self.lookup_field]
        try:
            validate_uuid(medical_id)
        except ValidationError:
            raise ValidationError("Invalid medical ID format.")
        queryset = self.get_queryset()
        filter_kwargs = {self.lookup_field: medical_id}
        try:
            obj = queryset.get(**filter_kwargs)
            return obj
        except Patient.DoesNotExist:
            if Patient.objects.filter(medical_id=medical_id).exists():
                raise NotFound("Patient does not exist in your organization.")
            raise NotFound("Patient with the specified medical ID was not found.")

    def update(self, request, *args, **kwargs):
        """
        Handle partial updates to patient details, including medical record.
        Returns the complete updated Patient object with all fields populated.
        """
        partial = kwargs.pop('partial', True)  # Default to partial updates
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Perform the update
        updated_instance = serializer.save()
        
        # Refresh from database to ensure we have the latest data
        updated_instance.refresh_from_db()
        
        # Create a fresh serializer instance to get the complete representation
        response_serializer = self.get_serializer(updated_instance)
        
        return Response(response_serializer.data, status=200)

    def perform_update(self, serializer):
        """
        Save the updated patient and medical record.
        """
        # This method is called by serializer.save() in the update method above
        return serializer.save()

    def patch(self, request, *args, **kwargs):
        """
        Handle PATCH requests for partial updates.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Handle PUT requests for full updates.
        """
        kwargs['partial'] = False
        return self.update(request, *args, **kwargs)


from rest_framework.views import APIView
from .serializers import PatientDiagnosisSerializer, SingleDiagnosisSerializer

# Alternative approach using separate endpoints (RECOMMENDED)
class PatientDiagnosisListView(ListAPIView):
    """
    Page 1: List of patients with their latest diagnosis only
    GET /api/patients/diagnoses/
    """
    serializer_class = PatientDiagnosisSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'medical_id']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_queryset(self):
        return (
            Patient.objects
            .prefetch_related(
                Prefetch(
                    'patientdiagnosisdetails_set',
                    queryset=PatientDiagnosisDetails.objects.select_related('caregiver').order_by('-created_at')
                )
            )
            .filter(patientdiagnosisdetails__isnull=False)
            .distinct()
            .order_by('-created_at')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['view_type'] = 'latest'
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Patients with latest diagnoses retrieved successfully",
            "data": response.data
        })

class PatientDiagnosisHistoryView(generics.RetrieveAPIView):
    """
    Get patient details with all their diagnoses
    GET /api/patients/{medical_id}/diagnoses/
    """
    serializer_class = PatientDiagnosisSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    lookup_field = 'medical_id'
    lookup_url_kwarg = 'medical_id'

    def get_queryset(self):
        """
        Return patients filtered by organization.
        """
        user = self.request.user
        if user.role == UserRoles.ORGANIZATION:
            organization = user.organization
        elif user.role == UserRoles.CAREGIVER:
            organization = user.caregiver.organization
        else:
            raise PermissionDenied("You do not have permission to access this resource.")
        
        if organization is None:
            raise NotFound("Organization not found for user.")
        
        return Patient.objects.filter(organization=organization)

    def get_object(self):
        """
        Get the patient object with their diagnoses.
        """
        queryset = self.get_queryset()
        medical_id = self.kwargs.get('medical_id')
        
        if not medical_id:
            raise PatientMedicalIDNotFoundException()
        
        try:
            patient = queryset.get(medical_id=medical_id)
        except Patient.DoesNotExist:
            raise PatientNotFoundException()
        
        return patient

    def retrieve(self, request, *args, **kwargs):
        """
        Return patient info with all their diagnoses.
        """
        patient = self.get_object()
        
        # Get all diagnoses for the patient (you can add filtering/ordering here if needed)
        diagnoses = PatientDiagnosisDetails.objects.filter(
            patient=patient
        ).select_related('caregiver', 'patient', 'organization').prefetch_related('vitalsign').order_by('-created_at')
        
        # Apply search filtering if search query is provided
        search_query = request.GET.get('search', None)
        if search_query:
            diagnoses = diagnoses.filter(
                Q(assessment__icontains=search_query) |
                Q(diagnoses__icontains=search_query) |
                Q(medication__icontains=search_query)
            )
        
        # Apply ordering if specified
        ordering = request.GET.get('ordering', '-created_at')
        if ordering:
            diagnoses = diagnoses.order_by(ordering)
        
        # Serialize the data
        patient_serializer = PatientDiagnosisSerializer(
            patient,
            context={'request': request, 'diagnoses_queryset': diagnoses}
        )
        
        return Response({
            'success': True,
            'message': 'Patient diagnosis history retrieved successfully',
            'data':  patient_serializer.data
        })




class SingleDiagnosisDetailView(RetrieveAPIView):
    """
    Page 3: Detailed view of a single diagnosis
    GET /api/diagnoses/{id}/
    """
    serializer_class = SingleDiagnosisSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    lookup_field = 'id'

    def get_queryset(self):
        return PatientDiagnosisDetails.objects.select_related(
            'patient', 'organization', 'caregiver'
        ).prefetch_related('vitalsign')

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Diagnosis details retrieved successfully",
            "data": response.data
        })
class CreatePatientDiagnosisWithVitalSignView(CreateAPIView):
    """
    Creates a new diagnosis and vital signs for a patient.
    """
    serializer_class = PatientDiagnosisWithVitalSignSerializer
    permission_classes = [IsAuthenticated, IsOrganization]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        caregiver_id = request.data.get('caregiver')
        if not caregiver_id:
            raise ValidationError("Caregiver ID is required")

        # Validate caregiver
        if not validate_uuid(caregiver_id):
            raise ValidationError("Caregiver ID is invalid")
        caregiver = get_object_or_404(Caregiver, id=caregiver_id, organization=self.request.user.organization)

        # Validate patient
        patient_id = self.kwargs['patient_id']
        if not validate_uuid(patient_id):
            raise ValidationError("Patient ID is invalid")
        patient = get_object_or_404(Patient, id=patient_id, organization=self.request.user.organization)

        # Validate and save serializer
        serializer.is_valid(raise_exception=True)
        serializer.save(organization=self.request.user.organization, patient=patient, caregiver=caregiver)

        response_data = {"message": "Patient diagnosis and vital signs created successfully", "data": serializer.data}
        return Response(response_data, status=status.HTTP_201_CREATED)


class UpdatePatientDiagnosisWithVitalSignView(UpdateAPIView):
    """
    Updates an existing diagnosis and vital signs for a patient.
    """
    serializer_class = PatientDiagnosisWithVitalSignSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    lookup_field = 'id'

    def get_queryset(self):
        return PatientDiagnosisDetails.objects.select_related(
            'patient', 'organization', 'caregiver'
        ).prefetch_related('vitalsign')

    def update(self, request, *args, **kwargs):
        diagnosis = self.get_object()
        caregiver_id = request.data.get('caregiver')
        if caregiver_id:
            if not validate_uuid(caregiver_id):
                raise ValidationError("Caregiver ID is invalid")
            caregiver = get_object_or_404(
                Caregiver, 
                id=caregiver_id, 
                organization=self.request.user.organization
            )
        else:
            caregiver = diagnosis.caregiver

        patient = get_object_or_404(
            Patient, 
            id=diagnosis.patient.id, 
            organization=self.request.user.organization
        )

        serializer = self.serializer_class(
            instance=diagnosis,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save(organization=self.request.user.organization, patient=patient, caregiver=caregiver)

        response_data = {
            "message": "Patient diagnosis and vital signs updated successfully",
            "data": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)





class PatientBasicInfoView(generics.RetrieveAPIView):
    """
    GET /patients/basic/<uuid:id>/
    Returns minimal patient info (e.g., full name, medical_id, profile_picture)
    Only if:
       • The requesting user is in the same organization (Org or Caregiver), or
       • The requesting user is that Patient themselves.
    """
    queryset = Patient.objects.all()
    serializer_class = PatientBasicInfoSerializer
    permission_classes = [IsAuthenticated,(IsOrganization | IsCaregiver | IsPatient)]
    lookup_field = 'id' 

    def get_queryset(self):
        user = self.request.user

        if user.role == UserRoles.ORGANIZATION:
            return Patient.objects.filter(organization=user.organization)

        if user.role == UserRoles.CAREGIVER:
            try:
                caregiver = Caregiver.objects.get(user=user)
            except Caregiver.DoesNotExist:
                raise PermissionDenied("You are not a valid caregiver.")
            return Patient.objects.filter(organization=caregiver.organization)

        if user.role == UserRoles.PATIENT:
            return Patient.objects.filter(user=user)
        raise PermissionDenied("You do not have permission to view patient data.")

    def get_object(self):
        patient_id = self.kwargs.get('id')

        try:
            validate_uuid(patient_id)
        except ValidationError:
            raise ValidationError("Invalid Patient ID format.")

        try:
            return super().get_object()
        except NotFound:
            raise PatientNotFoundException()
