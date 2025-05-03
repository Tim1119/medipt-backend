from rest_framework.permissions import BasePermission
from  apps.accounts.models import User
from rest_framework.exceptions import PermissionDenied
from apps.accounts.user_roles import UserRoles


class IsPatient(BasePermission):
    """Allows access only to patients for their own records."""
    def has_permission(self, request, view):
        return request.user and request.user.role == UserRoles.PATIENT

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsAllowedToUpdatePatientRegistrationDetails(BasePermission):

    """
    Allows updates if:
    - The user is a **patient** and is updating their own record.
    - The user is an **organization** and owns the patient.
    - The user is a **caregiver** and belongs to the same organization as the patient.
    """
       
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == UserRoles.PATIENT and obj.user == user:
            return True

        if user.role == UserRoles.ORGANIZATION and obj.organization == user.organization:
            return True
        

        if user.role == UserRoles.CAREGIVER and user.caregiver.organization == obj.organization:
            return True

        # return False 
        raise PermissionDenied("You are not authorized to update this patient’s details.")
    
    def has_permission(self, request, view):
        """Check if the user role is even allowed to attempt this action."""
        user = request.user

        if user.role in {UserRoles.PATIENT, UserRoles.ORGANIZATION, UserRoles.CAREGIVER}:
            return True  # Allow request to continue
        return False  # Block access before even fetching the object

   