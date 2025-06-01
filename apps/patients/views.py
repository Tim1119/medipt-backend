from django.shortcuts import render,get_object_or_404
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from .serializers import OrganizationRegisterPatientSerializer,PatientDetailSerializer,PatientSerializer,DiagnosisSerializer
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


# class PatientDiagnosisHistoryView(ListModelMixin, GenericAPIView):
#     """
#     Page 2: All diagnoses for a specific patient
#     GET /api/patients/{medical_id}/diagnoses/
#     """
#     serializer_class = PatientDiagnosisSerializer
#     permission_classes = [IsAuthenticated, IsOrganization]
#     pagination_class = StandardResultsSetPagination
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     search_fields = ['assessment', 'diagnoses', 'medication']
#     ordering_fields = ['created_at', 'assessment']
#     ordering = ['-created_at']

#     def get(self, request, *args, **kwargs):
#         return self.list(request, *args, **kwargs)

#     def get_queryset(self):
#         """
#         Filter patients to only those belonging to the organization of the authenticated user or caregiver.
#         """
#         user = self.request.user
#         if user.role == UserRoles.ORGANIZATION:
#             organization = user.organization
#         elif user.role == UserRoles.CAREGIVER:
#             organization = user.caregiver.organization
#         else:
#             raise PermissionDenied("You do not have permission to access this resource.")
        
#         if organization is None:
#             raise NotFound("Organization not found for user.")
        
#         medical_id = self.kwargs.get('medical_id')
#         if not medical_id:
#             # return Patient.objects.none()
#             raise PatientMedicalIDNotFoundException()
        
#         # Filter patients by organization and medical_id
#         return Patient.objects.filter(
#             organization=organization,
#             medical_id=medical_id
#         ).select_related('user').prefetch_related('patientmedicalrecord', 'patientdiagnosisdetails_set')

#     def list(self, request, *args, **kwargs):
#         medical_id = self.kwargs.get('medical_id')
        
#         # Check if patient exists and belongs to the organization
#         try:
#             patient = Patient.objects.get(
#                 medical_id=medical_id,
#                 organization=self.request.user.organization if self.request.user.role == UserRoles.ORGANIZATION else self.request.user.caregiver.organization
#             )
#         except Patient.DoesNotExist:
#             raise PatientNotFoundException()
        
#         # Use the Patient instance with the serializer
#         serializer = self.get_serializer(patient, context={'request': request, 'view_type': 'all'})
        
#         # Get the diagnoses queryset for counting and pagination
#         diagnoses_queryset = PatientDiagnosisDetails.objects.filter(
#             patient=patient
#         ).select_related('caregiver', 'patient', 'organization').prefetch_related('vitalsign')
        
#         # Apply filters to diagnoses queryset
#         diagnoses_queryset = self.filter_queryset(diagnoses_queryset)
        
#         # Paginate the diagnoses
#         page = self.paginate_queryset(diagnoses_queryset)
#         if page is not None:
#             diagnoses_serializer = DiagnosisSerializer(page, many=True, context={'request': request})
#             response = self.get_paginated_response(diagnoses_serializer.data)
#             patient_data = PatientDiagnosisSerializer(patient, context={'request': request})
#             response.data['patient_info'] = patient_data.data,
#             return response

#         # If not paginating, return all diagnoses
#         diagnoses_serializer = DiagnosisSerializer(diagnoses_queryset, many=True, context={'request': request})
#         patient_data = PatientDiagnosisSerializer(patient, context={'request': request})
#         return Response({
#             'success': True,
#             'message': 'Diagnosis history retrieved successfully',
#             'patient_info': patient_data.data,
#             'data': diagnoses_serializer.data
#         })
# class PatientDiagnosisHistoryView(generics.ListAPIView):
#     """
#     Alternative: List view without pagination
#     GET /api/patients/{medical_id}/diagnoses/
#     """
#     serializer_class = PatientDiagnosisSerializer
#     permission_classes = [IsAuthenticated, IsOrganization]
#     # Remove pagination
#     pagination_class = None
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     search_fields = ['assessment', 'diagnoses', 'medication']
#     ordering_fields = ['created_at', 'assessment']
#     ordering = ['-created_at']

#     def get_queryset(self):
#         """
#         This won't be used since we override list method
#         """
#         return PatientDiagnosisDetails.objects.none()

#     def list(self, request, *args, **kwargs):
#         """
#         Return patient info with all their diagnoses.
#         """
#         user = self.request.user
#         if user.role == UserRoles.ORGANIZATION:
#             organization = user.organization
#         elif user.role == UserRoles.CAREGIVER:
#             organization = user.caregiver.organization
#         else:
#             raise PermissionDenied("You do not have permission to access this resource.")
        
#         if organization is None:
#             raise NotFound("Organization not found for user.")
        
#         medical_id = self.kwargs.get('medical_id')
#         if not medical_id:
#             raise PatientMedicalIDNotFoundException()
        
#         # Get the patient
#         try:
#             patient = Patient.objects.get(
#                 medical_id=medical_id,
#                 organization=organization
#             )
#         except Patient.DoesNotExist:
#             raise PatientNotFoundException()
        
#         # Get all diagnoses for the patient
#         diagnoses_queryset = PatientDiagnosisDetails.objects.filter(
#             patient=patient
#         ).select_related('caregiver', 'patient', 'organization').prefetch_related('vitalsign')
        
#         # Apply filtering, searching, and ordering
#         diagnoses_queryset = self.filter_queryset(diagnoses_queryset)
        
#         # Serialize the patient with diagnoses
#         patient_serializer = PatientDiagnosisSerializer(
#             patient,
#             context={'request': request, 'diagnoses_queryset': diagnoses_queryset}
#         )
        
#         return Response({
#             'success': True,
#             'message': 'Patient diagnosis history retrieved successfully',
#             'data': patient_serializer.data
            
#         })

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









# class PatientUpdateRegistrationDetailsView(UpdateAPIView):
#     """
#     Helps to Update the registration details of patients when created by organization etc gender 
#     """ 
#     # queryset = Patient.objects.all()
#     serializer_class = UpdatePatientRegistrationDetailsSerializer
#     permission_classes = [IsAuthenticated,IsPatient | IsOrganization | IsCaregiver] 
#     lookup_field='id'

#     def get_queryset(self):
#         """Ensure the requesting user can only access patients they are allowed to update."""
#         user = self.request.user

#         if user.role == UserRoles.PATIENT:
#             return Patient.objects.filter(user=user)

#         elif user.role == UserRoles.ORGANIZATION:
#             return Patient.objects.filter(organization=user.organization)

#         elif user.role == UserRoles.CAREGIVER:
#             return Patient.objects.filter(organization=user.caregiver.organization)

#         return Patient.objects.none()  # Default to an empty queryset

#     def get_object(self):
#         patient_id = self.kwargs['id']

#         if not validate_uuid(patient_id):
#             raise ValidationError(f"Invalid Patient Id {patient_id}")

#         try:
#             return self.get_queryset().get(id=patient_id)
#         except Patient.DoesNotExist:
#             raise NotFound(detail="Patient with the given ID was not found or you do not have access.")


# class UpdatePatientBasicInfoView(UpdateAPIView):
#     """
#     Updates a patient's basic details: first name, last name, email, phone number, and address.
#     """
#     serializer_class = UpdatePatientBasicInfoSerializer
#     permission_classes = [IsAuthenticated,IsPatient | IsOrganization | IsCaregiver]
#     lookup_field='id'

#     def get_queryset(self):
#         """Ensure the requesting user can only access patients they are allowed to update."""
#         user = self.request.user

#         if user.role == UserRoles.PATIENT:
#             return Patient.objects.filter(user=user)

#         elif user.role == UserRoles.ORGANIZATION:
#             return Patient.objects.filter(organization=user.organization)

#         elif user.role == UserRoles.CAREGIVER:
#             return Patient.objects.filter(organization=user.caregiver.organization)

#         return Patient.objects.none()  # Default to an empty queryset
    
#     def get_object(self):
#         """Retrieve the patient by ID and validate ownership."""
#         patient_id = self.kwargs.get('id')

#         if not validate_uuid(patient_id):
#             raise ValidationError(f"Invalid Patient ID: {patient_id}")

#         try:
#             return self.get_queryset().get(id=patient_id)
#         except Patient.DoesNotExist:
#             raise NotFound(detail="Patient with the given ID was not found or you do not have access.")
    


# class PatientDetailView(RetrieveAPIView):
#     """
#     Retrieves detailed information for a specific patient associated with the authenticated organization
#     """
    
#     serializer_class = PatientDetailSerializer
#     permission_classes = [IsAuthenticated, IsOrganization]
    
#     def get_queryset(self):
#         """Filter patients to only those belonging to the organization of the authenticated user"""
#         return Patient.objects.filter(organization=self.request.user.organization)
    
    
# class PatientDetailByMedicalIDView(RetrieveAPIView):
#     """
#     Retrieves detailed information for a specific patient associated with the authenticated organization
#     """
    
#     serializer_class = PatientDetailSerializer
#     permission_classes = [IsAuthenticated, IsOrganization]
#     lookup_field = 'medical_id'
    
#     def get_queryset(self):
#         """Filter patients to only those belonging to the organization of the authenticated user"""
#         return Patient.objects.filter(organization=self.request.user.organization)
#     def get_object(self):
#         """
#         Override to customize the not found error message.
#         """
#         queryset = self.get_queryset()
#         filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
#         try:
#             obj = queryset.get(**filter_kwargs)
#         except Patient.DoesNotExist:
#             raise NotFound(detail="Patient with the specified medical ID was not found or does not belong to your organization.")
#         return obj
    
# class OrganizationUpdatePatientRegistrationDetailsView(UpdateAPIView):
#     """
#     Updates an existing patient's information associated with the authenticated organization
#     """
    
#     serializer_class = OrganizationUpdatePatientRegistrationDetailsSerializer
#     permission_classes = [IsAuthenticated, IsOrganization]
#     lookup_field = 'medical_id'
    
#     def get_queryset(self):
#         """Filter patients to only those belonging to the organization of the authenticated user"""
#         return Patient.objects.filter(organization=self.request.user.organization)
    
#     def get_object(self):
#         """
#         Override to customize the not found error message.
#         """
#         queryset = self.get_queryset()
#         filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
#         try:
#             obj = queryset.get(**filter_kwargs)
#         except Patient.DoesNotExist:
#             raise NotFound(detail="Patient with the specified medical ID was not found or does not belong to your organization.")
#         return obj
    
#     def perform_update(self, serializer):
#         with transaction.atomic():
#             patient = serializer.save()
#         return patient

# class PatientDetailByMedicalIDView(RetrieveAPIView):
#     """
#     Helps to Provide detailed information about the patient by medical id
#     """ 
#     serializer_class = PatientSerializer
#     permission_classes = [IsAuthenticated,IsPatient | IsOrganization | IsCaregiver]
#     lookup_field = 'medical_id'
#     # lookup_url_kwarg = 'id'  # Ensure this matches the URL pattern

#     def get_queryset(self):
#         """Ensure the requesting user can only access patients they are authorized to view."""
#         user = self.request.user

#         if user.role == UserRoles.PATIENT:
#             return Patient.objects.filter(user=user)

#         elif user.role == UserRoles.ORGANIZATION:
#             return Patient.objects.filter(organization=user.organization)

#         elif user.role == UserRoles.CAREGIVER:
#             return Patient.objects.filter(organization=user.caregiver.organization)

#         return Patient.objects.none()  # Default to an empty queryset
    
#     def get_object(self):
#         """
#         Override to customize the not found error message.
#         """
#         queryset = self.get_queryset()
#         filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
#         try:
#             obj = queryset.get(**filter_kwargs)
#         except Patient.DoesNotExist:
#             raise NotFound(detail="Patient with the specified medical ID was not found or does not belong to your organization.")
#         return obj


# class PatientDiagnosisDetailsRecordsView(RetrieveAPIView):
#     """
#     Helps to Provide diagnosis records and detail view for them if the id is sent in request
#     """ 
#     serializer_class = PatientDiagnosisDetailsSerializer
#     permission_classes = [IsAuthenticated,IsOrganization|IsCaregiver|IsPatient]
#     # lookup_field='id'

        
#     def get_queryset(self):
#         """Ensure the requesting user can only access patient diagnoses they are authorized to view."""
#         user = self.request.user
#         queryset = PatientDiagnosisDetails.objects.select_related("patient", "organization", "caregiver")

#         if user.role == UserRoles.PATIENT:
#             return queryset.filter(user=user)
#         if user.role == UserRoles.ORGANIZATION:
#             return queryset.filter(organization=user.organization)
#         if user.role == UserRoles.CAREGIVER:
#             return queryset.filter(organization=user.caregiver.organization)

#         return queryset.none()
        
#     def get_object(self):
#         """Retrieve a single diagnosis record if authorized."""
#         patient_diagnosis_details_id = self.kwargs.get('patient_diagnosis_details_id')

#         if not validate_uuid(patient_diagnosis_details_id):
#             raise ValidationError("Invalid Patient Health Record ID.")

#         try:
#             obj = self.get_queryset().get(id=patient_diagnosis_details_id)
#             self.check_object_permissions(self.request, obj)  # Enforce permissions at object level
#             return obj
#         except PatientDiagnosisDetails.DoesNotExist:
#             raise NotFound(detail="Diagnosis record not found.")


# class PatientDiagnosisListView(ListAPIView):
#     """
#     Provides a list of medical records for a specific patient.
#     Ensures only authorized users can access the records.
#     """
#     serializer_class = PatientDiagnosisListSerializer
#     permission_classes = [IsAuthenticated, IsOrganization | IsCaregiver | IsPatient]

#     def get_queryset(self):
#         """Retrieve patient diagnoses based on access permissions."""
#         user = self.request.user
#         medical_id = self.kwargs.get("medical_id")
#         diagnosis_queryset = PatientDiagnosisDetails.objects.select_related("organization", "caregiver")

#         if not medical_id:
#             raise ValidationError("Medical ID is required.")

#         # Validate the medical ID and ensure it belongs to a patient
#         patient = Patient.objects.filter(medical_id=medical_id).first()
#         if not patient:
#             raise NotFound("Patient with the specified medical ID was not found.")

#         # Patient-specific flow (returns only their own diagnoses)
#         if user.role == UserRoles.PATIENT:
#             if patient.id != user.patient.id:
#                 raise NotFound("You do not have permission to access this patient's records.")
#             return Patient.objects.filter(
#                 id=patient.id,
#                 patientdiagnosisdetails__isnull=False
#             ).distinct().prefetch_related(
#                 Prefetch("patientdiagnosisdetails_set", queryset=diagnosis_queryset.filter(organization=patient.organization))
#             )

#         # Organization-specific flow (can view only patients within their organization)
#         if user.role == UserRoles.ORGANIZATION:
#             if patient.organization != user.organization:
#                 raise NotFound("Patient does not belong to your organization.")
#             return Patient.objects.filter(
#                 id=patient.id,
#                 patientdiagnosisdetails__isnull=False
#             ).distinct().prefetch_related(
#                 Prefetch("patientdiagnosisdetails_set", queryset=diagnosis_queryset.filter(organization=user.organization))
#             )

#         # Caregiver-specific flow (can only view patients assigned to them)
#         if user.role == UserRoles.CAREGIVER:
#             if patient.organization != user.caregiver.organization:
#                 raise NotFound("Patient does not belong to your organization.")
#             return Patient.objects.filter(
#                 id=patient.id
#             ).prefetch_related(
#                 Prefetch("patientdiagnosisdetails_set", queryset=diagnosis_queryset.filter(caregiver=user.caregiver))
#             )

#         return Patient.objects.none()

#     def get_object(self):
#         """
#         Override to customize the not found error message.
#         Ensures the medical ID belongs to a valid patient.
#         """
#         queryset = self.get_queryset()
#         medical_id = self.kwargs.get("medical_id")

#         if not medical_id:
#             raise ValidationError("Medical ID is required.")

#         # Ensure the medical ID is linked to a valid patient
#         patient = Patient.objects.filter(medical_id=medical_id).first()
#         if not patient:
#             raise NotFound("Patient with the specified medical ID was not found.")

#         # Retrieve the object using the medical ID
#         try:
#             obj = queryset.get(medical_id=medical_id)
#         except Patient.DoesNotExist:
#             raise NotFound("Medical record not found or does not belong to the specified patient.")

#         return obj

# class CreatePatientDiagnosisWithVitalSignView(CreateAPIView):
#     """
#     Allows an organization or a caregiver to create a new diagnosis and vital signs for a patient.

#     Rules:
#     - If used by an organization: Requires both `caregiver_id` and `patient_id`.
#     - If used by a caregiver: Automatically assigns the caregiver; ensures the patient is in the same organization.
#     """
#     serializer_class = CreatePatientDiagnosisWithVitalSignSerializer
#     permission_classes = [IsAuthenticated, IsOrganization | IsCaregiver]

#     def get_patient(self, user, patient_id):
#         """Retrieve and validate the patient."""
#         if not validate_uuid(patient_id):
#             raise ValidationError("Invalid Patient ID format.")
#         try:
#             return Patient.objects.get(id=patient_id)
#         except Patient.DoesNotExist:
#             raise NotFound(f"Patient with ID {patient_id} not found.")

#     def get_caregiver(self, user, caregiver_id):
#         """Retrieve and validate the caregiver (only for organization users)."""
#         if not validate_uuid(caregiver_id):
#             raise ValidationError("Invalid Caregiver ID format.")
#         try:
#             return Caregiver.objects.get(id=caregiver_id, organization=user.organization)
#         except Caregiver.DoesNotExist:
#             raise NotFound(f"Caregiver with ID {caregiver_id} not found in your organization.")

#     def perform_create(self, serializer):
#         """Handles creation logic based on user role."""
#         user = self.request.user
#         patient_id = self.kwargs.get("patient_id")
#         patient = self.get_patient(user, patient_id)

#         # Organization user: Requires caregiver_id
#         if user.role == UserRoles.ORGANIZATION:
#             caregiver_id = self.request.data.get("caregiver")
#             if not caregiver_id:
#                 raise ValidationError("Caregiver ID is required when an organization creates a diagnosis.")
#             caregiver = self.get_caregiver(user, caregiver_id)

#         # Caregiver user: Must be assigned automatically & match patient's organization
#         elif user.role == UserRoles.CAREGIVER:
#             caregiver = user.caregiver
#             if patient.organization != caregiver.organization:
#                 raise ValidationError("You can only create diagnoses for patients within your organization.")

#         else:
#             raise ValidationError("Only organizations and caregivers can create patient diagnoses.")

#         # Final organization match check
#         if patient.organization != caregiver.organization:
#             raise ValidationError("Patient and caregiver must belong to the same organization.")

#         serializer.save(organization=patient.organization, patient=patient, caregiver=caregiver)

#     def create(self, request, *args, **kwargs):
#         """Override create method for a consistent response format."""
#         response = super().create(request, *args, **kwargs)
#         return Response(
#             {"message": "Patient diagnosis and vital signs created successfully", "data": response.data},
#             status=status.HTTP_201_CREATED
#         )

