from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from apps.organizations.validators import validate_organization_acronym
from rest_framework import serializers
from .user_roles import UserRoles
from apps.organizations.models import Organization, User  
import logging
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

class OrganizationSignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, validators=[validate_password])
    acronym = serializers.CharField(max_length=10, min_length=2, validators=[validate_organization_acronym])

    user_email = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Organization
        fields = ['id', 'name', 'acronym', 'email', 'password','user_email']
        read_only_fields = ['id','user_email']

    def get_user_email(self, obj):
        return obj.user.email

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
       
    def validate_acronym(self, value):
        if Organization.objects.filter(acronym=value).exists():
            raise serializers.ValidationError("An organization with this acronym already exists.")
        return value
       

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated_data['email'],
                    password=validated_data['password'],
                    role=UserRoles.ORGANIZATION
                )

                organization = Organization.objects.create(
                    user=user,
                    name=validated_data['name'].title(),
                    acronym=validated_data['acronym'],
                )
            return organization

        except IntegrityError as e:
            logger.error(f"Database error during organization creation: {e}", exc_info=True)
            raise serializers.ValidationError("A database integrity error occurred. Please check the data and try again.")

        except ValidationError as e:
            logger.warning(f"Validation error: {e}", exc_info=True)
            raise serializers.ValidationError(e.messages) 

        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            raise serializers.ValidationError("An unexpected error occurred. Please try again later.")


# from rest_framework import serializers


# from users.models import User

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    id = serializers.UUIDField(read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')

        # Authenticate user using Django authentication framework
        user = authenticate(email=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationFailed("Your account is not yet activated. Please check your email.")

        if not user.is_verified:
            raise AuthenticationFailed("Your account is not verified. Please check your email.")

        # Generate JWT tokens using SimpleJWT
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return {
            "email": user.email,
            "role": user.role if user.role else "Admin",
            "id": user.id,
            "refresh_token": str(refresh),
            "access_token": str(access),
            "full_name":user.get_full_name,
        }


# class ResendActivationSerializer(serializers.Serializer):
#     email = serializers.EmailField()
