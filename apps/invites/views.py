import uuid
import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.organizations.permissions import IsOrganization
from .models import CaregiverInvite, InvitationStatus
from .serializers import CaregiverAcceptInvitationSerializer, CaregiverInvitationSerializer
from .tasks import send_invitation_to_caregiver
from shared.validators import validate_uuid
from .exceptions import (
    CaregiverInvitationException,
    ActiveInvitationExistsException,
    InvitationAlreadyAcceptedException,
    MaxResendsExceededException,
    InvalidInvitationTokenException,
    InvitationNotFoundException,
    InvitationExpiredException,
    EmailSendingFailedException,
)

logger = logging.getLogger(__name__)

class InviteCaregiverView(APIView):
    """
    Allows an organization to invite a caregiver via email.
    - Prevents duplicate invitations.
    - Updates and resends expired invitations.
    - Limits resends to prevent abuse.
    """
    permission_classes = [IsAuthenticated, IsOrganization]
    throttle_classes = [UserRateThrottle]  # Rate limit to prevent abuse

    @swagger_auto_schema(
        request_body=CaregiverInvitationSerializer,
        responses={
            201: openapi.Response("Invitation sent successfully"),
            400: openapi.Response("Validation error or invitation already exists"),
        },
    )
    def post(self, request):
        serializer = CaregiverInvitationSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            raise CaregiverInvitationException(detail=serializer.errors)

        email = serializer.validated_data["email"]
        organization = serializer.validated_data["organization"]
        role = serializer.validated_data["role"]
        max_resends = getattr(settings, "MAX_INVITATION_RESENDS", 3)

        try:
            with transaction.atomic():
                # Check for existing invitation
                existing_invite = CaregiverInvite.objects.filter(
                    email__iexact=email,
                    organization=organization,
                    is_deleted=False
                ).first()

                if existing_invite:
                    if existing_invite.status == InvitationStatus.ACCEPTED:
                        raise InvitationAlreadyAcceptedException()
                    if existing_invite.resend_count >= max_resends:
                        raise MaxResendsExceededException()
                    if not existing_invite.is_expired():
                        raise ActiveInvitationExistsException()
                    # Update expired invitation
                    existing_invite.token = uuid.uuid4()
                    existing_invite.expires_at = default_expires_at()
                    existing_invite.resend_count += 1
                    existing_invite.status = InvitationStatus.PENDING
                    existing_invite.invited_by = request.user
                    existing_invite.save()
                    invitation = existing_invite
                else:
                    # Create new invitation
                    invitation = serializer.save(invited_by=request.user)

            # Send invitation asynchronously
            try:
                send_invitation_to_caregiver.delay(
                    email=invitation.email,
                    invitation_token=str(invitation.token),
                    role=invitation.role,
                    organization_name=invitation.organization.name,
                )
                logger.info(
                    f"Invitation sent to {invitation.email} for role {invitation.role} by user {request.user.id}"
                )
            except Exception as e:
                logger.error(f"Failed to queue invitation email for {invitation.email}: {str(e)}")
                raise EmailSendingFailedException(
                    detail={
                        "message": "Invitation created, but email sending failed.",
                        "invitation_id": str(invitation.id),
                    }
                )

            return Response(
                {
                    "message": "Invitation sent successfully.",
                    "invitation_id": str(invitation.id),
                    "email": invitation.email,
                    "role": invitation.role,
                    "status": invitation.status,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            if not isinstance(e, CustomValidationError):
                raise CaregiverInvitationException(
                    detail=f"An unexpected error occurred: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                ) from e
            raise

class CaregiverAcceptInvitationView(CreateAPIView):
    """
    Handles caregiver invitation acceptance by creating a user account.
    Validates token and invitation status before proceeding.
    """
    serializer_class = CaregiverAcceptInvitationSerializer
    throttle_classes = [UserRateThrottle]  # Rate limit to prevent brute-force attacks

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="token",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="The unique invitation token (UUID)",
                required=True,
            )
        ],
        request_body=CaregiverAcceptInvitationSerializer,
        responses={
            201: openapi.Response("Caregiver account created successfully"),
            400: openapi.Response("Validation error"),
            404: openapi.Response("Invalid or expired invitation"),
        },
    )
    def post(self, request, *args, **kwargs):
        token = self.kwargs.get("token")
        if not validate_uuid(token):
            raise InvalidInvitationTokenException()

        try:
            with transaction.atomic():
                try:
                    invitation = CaregiverInvite.objects.filter(
                        token=token,
                        is_deleted=False
                    ).select_for_update().get()
                except CaregiverInvite.DoesNotExist:
                    raise InvitationNotFoundException()

                if invitation.is_expired():
                    invitation.status = InvitationStatus.EXPIRED
                    invitation.save()
                    raise InvitationExpiredException()
                if invitation.status != InvitationStatus.PENDING:
                    raise InvitationAlreadyAcceptedException()

                # Proceed with serializer to create user
                serializer = self.get_serializer(data=request.data, context={"token": token})
                if not serializer.is_valid():
                    raise CaregiverInvitationException(detail=serializer.errors)
                user = serializer.save()

                # Update invitation status
                invitation.status = InvitationStatus.ACCEPTED
                invitation.save()

                logger.info(
                    f"Invitation accepted for {invitation.email} by user {user.id} in organization {invitation.organization.name}"
                )

            return Response(
                {
                    "message": "Caregiver account created successfully.",
                    "user_id": str(user.id),
                    "email": invitation.email,
                    "organization": invitation.organization.name,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            if not isinstance(e, CustomValidationError):
                raise CaregiverInvitationException(
                    detail=f"An unexpected error occurred: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                ) from e
            raise

    def get_serializer_context(self):
        """Include token in serializer context."""
        context = super().get_serializer_context()
        context["token"] = self.kwargs.get("token")
        return context