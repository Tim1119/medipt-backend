from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from apps.accounts.models import User
from apps.caregivers.models import Caregiver
from apps.accounts.user_roles import UserRoles
from .models import CaregiverInvite, InvitationStatus
from .exceptions import (
    CaregiverInvitationException,
    ActiveInvitationExistsException,
    InvitationAlreadyAcceptedException,
    InvitationNotFoundException,
    InvitationExpiredException,
    InvalidInvitationTokenException,
)

class CaregiverInvitationSerializer(serializers.ModelSerializer):
    """Serializer to validate and process caregiver invitations."""
    
    class Meta:
        model = CaregiverInvite
        fields = ["email", "role"]

    def validate_email(self, value):
        """Validate the email and check for existing users or invitations."""
        email = value.lower()  # Normalize to lowercase
        request = self.context["request"]
        organization = request.user.organization

        # Check if a user with this email already exists
        if User.objects.filter(email__iexact=email).exists():
            raise CaregiverInvitationException(
                detail="A user with this email already exists.",
                code="user_already_exists"
            )

        # Check for existing invitation in the same organization
        invitation = CaregiverInvite.objects.filter(
            email__iexact=email,
            organization=organization
        ).first()  # Removed deleted_at__isnull=True

        if invitation:
            if invitation.status == InvitationStatus.ACCEPTED:
                raise InvitationAlreadyAcceptedException()
            if invitation.status == InvitationStatus.PENDING and not invitation.is_expired():
                raise ActiveInvitationExistsException()

        return email

    def create(self, validated_data):
        """Create a new invitation with the requesting user as invited_by."""
        validated_data["organization"] = self.context["request"].user.organization
        validated_data["invited_by"] = self.context["request"].user
        return super().create(validated_data)

class CaregiverAcceptInvitationSerializer(serializers.Serializer):
    """Serializer to validate and process caregiver invitation acceptance."""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirmation = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        fields = ["first_name", "last_name", "password", "password_confirmation"]

    def validate(self, data):
        """Validate the invitation token and input data."""
        if data["password"] != data["password_confirmation"]:
            raise CaregiverInvitationException(
                detail={"password_confirmation": "Passwords do not match."},
                code="password_mismatch"
            )

        token = self.context.get("token")
        if not token:
            raise InvalidInvitationTokenException()

        invitation = CaregiverInvite.objects.filter(
            token=token
        ).first()  # Removed deleted_at__isnull=True

        if not invitation:
            raise InvitationNotFoundException()

        if invitation.status != InvitationStatus.PENDING:
            raise InvitationAlreadyAcceptedException()
        if invitation.is_expired():
            invitation.status = InvitationStatus.EXPIRED
            invitation.save()
            raise InvitationExpiredException()

        if Caregiver.objects.filter(user__email__iexact=invitation.email).exists():
            raise CaregiverInvitationException(
                detail="A caregiver account already exists for this email.",
                code="caregiver_already_exists"
            )

        self.context["invitation"] = invitation
        return data

    def create(self, validated_data):
        """Create a caregiver account upon successful invitation acceptance."""
        invitation = self.context["invitation"]

        with transaction.atomic():
            user = User.objects.create_user(
                email=invitation.email,
                role=UserRoles.CAREGIVER,
                password=validated_data["password"],
                is_invited=True,
                is_active=True,
                is_verified=True,
            )

            caregiver = Caregiver.objects.create(
                user=user,
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                organization=invitation.organization,
                caregiver_type=invitation.role
            )

            invitation.status = InvitationStatus.ACCEPTED
            invitation.save()

        return caregiver