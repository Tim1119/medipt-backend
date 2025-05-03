from rest_framework.permissions import BasePermission
from  apps.accounts.models import User
from rest_framework.exceptions import PermissionDenied
from apps.accounts.user_roles import UserRoles


class IsOrganization(BasePermission):
    """
    Allows access only to users with the organization role.
    """
    message = "You do not have permission to access this data."

    def has_permission(self, request, view):
        return request.user and request.user.role == UserRoles.ORGANIZATION

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.role == UserRoles.ORGANIZATION


class IsOrganizationAndOwnsObject(BasePermission):
    """
    Checks if the authenticated user is an organization and owns the requested object.
    """

    def has_object_permission(self, request, view, obj):
        """
        Checks if the object belongs to the requesting organization user.
        """
        if request.user.role == UserRoles.ORGANIZATION and obj.user == request.user:
            return True  # The organization owns the object
        raise PermissionDenied("You do not have permission to access this data.")

    def has_permission(self, request, view):
        """
        Allows request only if the user is authenticated and an organization.
        """
        return request.user.is_authenticated and request.user.role == UserRoles.ORGANIZATION