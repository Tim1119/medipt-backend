from rest_framework import status
from shared.custom_validation_error import CustomValidationError


class PatientNotificationFailedException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Failed to send notification to the user."
    default_code = "patient_notification_failed"