from rest_framework.permissions import BasePermission
from apps.accounts.user_roles import UserRoles

class IsCaregiver(BasePermission):
    """Allows access to caregivers within their organization."""
    def has_permission(self, request, view):
        return request.user and request.user.role == UserRoles.CAREGIVER

    def has_object_permission(self, request, view, obj):
        return obj.organization == request.user.caregiver.organization