from shared.custom_validation_error import CustomValidationError
from rest_framework import generics, status


class PatientNotFoundException(CustomValidationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Patient not Found"
    default_code = "organization_patient_details_not_found"

class PatientDiagnosisDetailsNotFoundException(CustomValidationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Patient Diagnosis Details not Found"
    default_code = "organization_patient_diagnoses details not found"
