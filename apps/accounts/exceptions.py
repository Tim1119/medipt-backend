from rest_framework import status
from shared.custom_validation_error import CustomValidationError


class OrganizationSignupException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Failed to register organization."
    default_code = "organization_registration_failed"
    
class ActivationLinkExpiredException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Activation link has expired."
    default_code = "account_activation_link_expired"

class AccountAlreadyActiveException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Account is already active."
    default_code = "account_already_active"

class InvalidActivationTokenException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid activation token."
    default_code = "account_invalid_token"

class UserDoesNotExistException(CustomValidationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "User not found."
    default_code = "account_user_not_found"

class LoginAccountException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An error occurred during login."
    default_code = "account_login_error"

class InvalidLoginCredentialsException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid email or password."
    default_code = "account_invalid_login_credentials"
class InvalidRefreshTokenException(CustomValidationError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid or expired refresh token."
    default_code = "invalid_refresh_token"

class InvalidPasswordResetTokenException(CustomValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired password reset token."
    default_code = "invalid_password_reset_token"
