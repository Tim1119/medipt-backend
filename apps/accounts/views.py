from rest_framework import generics, status
from rest_framework.response import Response
from shared.custom_validation_error import CustomValidationError
from .serializers import OrganizationSignupSerializer,LoginSerializer
from .models import User
from apps.accounts.tasks import send_organization_activation_email,send_password_reset_email
from django.contrib.sites.shortcuts import get_current_site
import jwt
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .user_roles import UserRoles
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .exceptions import (OrganizationSignupException,ActivationLinkExpiredException,
InvalidActivationTokenException,UserDoesNotExistException,AccountAlreadyActiveException,
InvalidLoginCredentialsException,LoginAccountException,InvalidRefreshTokenException,InvalidPasswordResetTokenException
)
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from django.contrib.auth.password_validation import validate_password
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView

from datetime import timedelta
from django.middleware.csrf import get_token
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
# Create your views here.
class OrganizationSignupView(generics.GenericAPIView):
    serializer_class = OrganizationSignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                organization = serializer.save()
                organization_user = organization.user
                organization_email = organization_user.email
                current_site_domain = get_current_site(request).domain
                send_organization_activation_email.delay(current_site_domain, organization_email)
    
                return Response({"message": "Organization registered successfully","data":serializer.data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                raise OrganizationSignupException(detail=e.add_note("An unexpected error occurred. Please try again later."))
        else:
            raise OrganizationSignupException(detail=serializer.errors)

class VerifyAccount(APIView):
    """
    Verifies user account using a token.
    """
    
    def get(self, request, token):
        if not token:
            raise CustomValidationError("Token is required")
            
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

            # Ensure "user_id" exists in payload
            user_id = payload.get('user_id')
            if not user_id:
                raise CustomValidationError(detail="Invalid token payload: user data missing")

            # Fetch user
            user = User.objects.get(id=user_id)

            # Handle already active accounts as a success case, not an error
            if user.is_active:
                return Response({
                    "success": True, 
                    "message": "Account is already active.",
                    "already_active": True
                }, status=status.HTTP_200_OK)

            # Activate user
            user.is_verified = True
            user.is_active = True

            # Define success messages based on role
            role_messages = {
                UserRoles.ORGANIZATION: _("Organization account successfully activated"),
                UserRoles.PATIENT: _("Patient account successfully activated"),
                UserRoles.CAREGIVER: _("Caregiver account successfully activated"),
                UserRoles.ORGANIZATION_ADMIN: _("Organization Admin successfully activated"),
            }

            message = role_messages.get(user.role, _("Account successfully activated"))
            user.save()

            return Response({"success": True, "message": message}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            raise ActivationLinkExpiredException()

        except jwt.InvalidTokenError:
            raise InvalidActivationTokenException()

        except User.DoesNotExist:
            raise UserDoesNotExistException()

        except Exception as e:
            raise CustomValidationError(detail=f"An unexpected error occurred: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) 


class LoginAccountView(generics.GenericAPIView):
    throttle_classes = [AnonRateThrottle]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        response = Response({"message": "Login successful",**serializer.validated_data}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=serializer.validated_data["access_token"],
            httponly=True,  # Prevent JavaScript access (XSS protection)
            secure=False,  # Use False for local development (True for production with HTTPS)
            samesite="Lax",  # Prevent CSRF attacks
            max_age=timedelta(days=7).total_seconds(),  # 7 days expiration
        )
        response.set_cookie(
            key="refresh_token",
            value=serializer.validated_data["refresh_token"],
            httponly=True,
            secure=False,  # Set True in production
            samesite="Lax",
        )

        # TODO: Change secure to true before deployment in production

        # Set CSRF Token in response header
        response["X-CSRFToken"] = get_token(request)

        return response




class ResendActivationLinkView(APIView): 

    """
    Allows users to request a new activation email if they haven't activated their account yet.
    """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='Email address to resend activation link'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Activation link resent successfully",
                examples={
                     "message": "Activation link has been resent. Please check your email"
                }
            ),
            400: openapi.Response(description="Validation Error"),
            404: openapi.Response(description="User Not Found")
        }
    )

    def post(self, request):
        email = request.data.get('email')
        if not email:
            raise ValidationError({"Email is required"})

        try:
            user = User.objects.get(email=email)

            if user.is_active and user.is_verified:
                raise AccountAlreadyActiveException()

            current_site_domain = get_current_site(request).domain

            send_organization_activation_email.delay(current_site_domain, email)

            return Response({"message": "Activation link has been resent. Please check your email"},status=status.HTTP_200_OK)

        except User.DoesNotExist:
            raise UserDoesNotExistException()
        
class LogoutView(APIView):

    """
    Logs out a user by blacklisting their refresh token.
    """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh_token"],
            properties={
                "refresh_token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="JWT Refresh Token to be blacklisted",
                    example="your-refresh-token-here"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Successfully logged out",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Successfully logged out")
                    }
                )
            ),
            400: openapi.Response(description="Validation Error - Refresh token is required"),
            401: openapi.Response(description="Invalid or Expired Refresh Token"),
        }
    )
    
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            raise ValidationError("Refresh token is required.")

        try:
            RefreshToken(refresh_token).blacklist()
            return Response({"message": "Successfully logged out"}, status=200)
        
        except TokenError:
            raise InvalidRefreshTokenException(detail="Isdafakdmakdsmnvalid or expired refresh token")
        except Exception:
            raise InvalidRefreshTokenException()

class PasswordResetRequestView(APIView):

    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            send_password_reset_email.delay(user.email)
            return Response({"message": "Password reset link sent","data":email}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            raise UserDoesNotExistException()

class PasswordResetConfirmView(APIView):

    def post(self, request):
        token = request.data.get("reset_token")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not token or not new_password or not confirm_password:
            raise InvalidPasswordResetTokenException("Token, new password, and confirmation password are required.")

        if new_password != confirm_password:
            raise InvalidPasswordResetTokenException("Passwords do not match.")

        try:
            # Decode the token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])

            # Validate the password using Django's built-in validators
            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                raise InvalidPasswordResetTokenException(e.messages[0])

            # Set the new password and save the user
            user.set_password(new_password)
            user.save()
            user.refresh_from_db()

            print(f"New password hash: {user.password}")


            return Response({"message": "Password successfully reset"}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            raise InvalidPasswordResetTokenException("Token has expired.")

        except jwt.DecodeError:
            raise InvalidPasswordResetTokenException("Invalid token format.")

        except User.DoesNotExist:
            raise InvalidPasswordResetTokenException("User not found.")
        
class ChangePasswordView(APIView):
    """
    Allows a logged-in user to change their password by providing the current password,
    new password, and password confirmation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            raise CustomValidationError("All fields are required: current_password, new_password, confirm_password.")

        if new_password != confirm_password:
            raise CustomValidationError("New passwords do not match.")

        if not user.check_password(current_password):
            raise CustomValidationError("Current password is incorrect.")

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            raise CustomValidationError(e.messages[0])

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
