from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from .serializers import CaregiverSerializer
from rest_framework.generics import ListAPIView,CreateAPIView,UpdateAPIView,RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOrganizationOrCaregiver
from apps.accounts.user_roles import UserRoles
from .models import Caregiver
from apps.organizations.permissions import IsOrganization
from rest_framework.mixins import RetrieveModelMixin,UpdateModelMixin,DestroyModelMixin,ListModelMixin
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from shared.pagination import StandardResultsSetPagination
from .exceptions import CaregiverNotFoundException


# Create your views here.
class LatestCaregiversView(ListAPIView):
    """
    Lists the 5 most recently hired caregivers in the authenticated user's organization
    (whether the user is an organization or a caregiver).
    """
    # permission_classes = [IsAuthenticated, IsOrganizationOrCaregiver]
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = CaregiverSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == UserRoles.ORGANIZATION:
            organization = user.organization
        # elif user.role == UserRoles.CAREGIVER:
        #     organization = user.caregiver.organization
        else:
            raise NotFound("Organization not found for user.")

        if organization is None:
            raise NotFound("Organization not found for user.")

        return Caregiver.objects.filter(organization=organization,user__is_verified=True,user__is_active=True,user__role=UserRoles.CAREGIVER)[:5]

class CaregiverViewSet(ListModelMixin,RetrieveModelMixin,UpdateModelMixin,DestroyModelMixin,viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsOrganization]
    serializer_class = CaregiverSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['first_name', 'last_name', 'staff_number']
    filterset_fields = ['caregiver_type', 'user__is_active']
    pagination_class = StandardResultsSetPagination
    lookup_field = 'slug'
    

    def get_queryset(self):
        user = self.request.user

        if user.role == UserRoles.ORGANIZATION:
            organization = user.organization
        # elif user.role == UserRoles.CAREGIVER:
        #     organization = user.caregiver.organization

        else:
            raise NotFound("Organization not found for user.")

        if organization is None:
            raise NotFound("Organization not found for user.")

        return Caregiver.objects.filter(organization=organization,user__is_verified=True,user__is_active=True,user__role=UserRoles.CAREGIVER)

    

class ToggleCaregiverStatusView(UpdateAPIView):
    """
    Helps to toggle the status of the caregiver from active to non-active and vice versa
    """ 
    model = Caregiver
    serializer_class = CaregiverSerializer
    permission_classes = [IsAuthenticated, IsOrganization]
    lookup_field='slug'

    def get_object(self):
        caregiver_slug = self.kwargs['slug']
        caregiver = Caregiver.objects.filter(slug=caregiver_slug, organization=self.request.user.organization).first()
        if not caregiver:
            raise CaregiverNotFoundException()
        return caregiver
    
    def update(self, request, *args, **kwargs):
        caregiver = self.get_object()
        caregiver.user.is_active = not caregiver.user.is_active
        caregiver.user.save() 
        serializer = CaregiverSerializer(caregiver,many=False)
        return Response({ "message": "Caregiver status toggled successfully", "data": serializer.data},status=status.HTTP_200_OK)
    







# class LatestCaregiverListView(ListAPIView):
#     """
#     Lists the 4 most recently hired caregivers for the organization.
#     """
#     permission_classes = [IsAuthenticated, IsOrganizationCaregiverAccess]
#     serializer_class = CaregiverSerializer

#     def get_queryset(self):
#         if not self.request.user.organization:
#             raise NotFound("Organization not found for user.")
#         return Caregiver.objects.filter(
#             organization=self.request.user.organization,
#             is_active=True,
#             user__is_verified=True
#         ).order_by('-hire_date', '-created_at')[:4]


# class OrganizationLatestCaregiversListView(ListAPIView):
#     """
#     Lists top 10 latest caregivers associated with the authenticated organization based on filter criteria.
#     """
#     permission_classes = [IsAuthenticated, IsOrganization]
#     serializer_class = CaregiverSerializer

#     def get_queryset(self):
#         if self.request.user.organization is None:
#             raise NotFound("Organization not found for user.")
#         return Caregiver.objects.filter(organization=self.request.user.organization,user__is_active=True,user__is_verified=True)[:10]
    


# class OrganizationCaregiversListView(ListAPIView):
#     """
#     Lists caregivers associated with the authenticated organization based on filter criteria.
#     """
#     permission_classes = [IsAuthenticated, IsOrganization]
#     serializer_class = CaregiverSerializer
#     # pagination_class = StandardResultsSetPagination
#     # filter_backends = [SearchFilter]
#     # search_fields = ['first_name', 'last_name', 'staff_number', 'caregiver_type']

#     def get_queryset(self):
#         if self.request.user.organization is None:
#             raise NotFound("Organization not found for user.")
#         return Caregiver.objects.filter(organization=self.request.user.organization,user__is_active=True,user__is_verified=True)

