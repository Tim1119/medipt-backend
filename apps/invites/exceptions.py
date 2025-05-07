from rest_framework import status
from shared.custom_validation_error import CustomValidationError

class CaregiverInvitationException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Failed to send caregiver invitation."
    default_code = "caregiver_invitation_failed"

class ActiveInvitationExistsException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An active invitation already exists for this email."
    default_code = "active_invitation_exists"

class InvitationAlreadyAcceptedException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invitation has already been accepted."
    default_code = "invitation_already_accepted"

class MaxResendsExceededException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Maximum resend limit reached for this invitation."
    default_code = "max_resends_exceeded"

class InvalidInvitationTokenException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid invitation token."
    default_code = "invalid_invitation_token"

class InvitationNotFoundException(CustomValidationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Invitation not found."
    default_code = "invitation_not_found"

class InvitationExpiredException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invitation has expired."
    default_code = "invitation_expired"

class EmailSendingFailedException(CustomValidationError):
    status_code = status.HTTP_201_CREATED  # Still create invitation, but warn about email failure
    default_detail = "Invitation created, but email sending failed. Please try again later."
    default_code = "email_sending_failed"