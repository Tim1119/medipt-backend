from rest_framework.permissions import BasePermission
from apps.accounts.user_roles import UserRoles

class IsCaregiver(BasePermission):
    """Allows access to caregivers within their organization."""
    def has_permission(self, request, view):
        return request.user and request.user.role == UserRoles.CAREGIVER

    def has_object_permission(self, request, view, obj):
        return obj.organization == request.user.caregiver.organization

class IsOrganizationOrCaregiver(BasePermission):
    """
    Allows access to authenticated users who are either organization users or caregivers belonging to the organization.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == UserRoles.CAREGIVER  or request.user.role == UserRoles.ORGANIZATION))
