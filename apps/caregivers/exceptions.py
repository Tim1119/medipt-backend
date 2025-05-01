from shared.custom_validation_error import CustomValidationError
from rest_framework import generics, status


class CaregiverNotFoundException(CustomValidationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Caregiver not Found"
    default_code = "organization_caregiver_not_found"
