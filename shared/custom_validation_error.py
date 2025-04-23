from rest_framework.exceptions import APIException

class CustomValidationError(APIException):
    """
    Custom exception to handle validation errors with a consistent structure.
    """
    status_code = 400
    default_detail = "Validation error occurred."
    default_code = "validation_error"

    def __init__(self, detail=None, status_code=None):
        if status_code:
            self.status_code = status_code
        detail = detail or self.default_detail
        super().__init__(detail)  
