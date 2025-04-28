from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from apps.organizations.models import Organization
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import datetime, timedelta,timezone
from .exceptions import UserDoesNotExistException
import jwt

@shared_task
def send_organization_activation_email(current_site,organization_email):
    organization = Organization.objects.get(user__email=organization_email)
    token = RefreshToken.for_user(organization.user).access_token
    activation_link = f"{settings.REACT_FRONTEND_URL}/auth/verify-email/{str(token)}"

    context = {
        'organization_name': organization.name,
        'activation_link': activation_link,
        'current_site': current_site,
    }
    
    subject = 'Activate Your Organization Account'

    html_message = render_to_string('accounts/organizations/organization_activation_email.html', context)
    from_email = settings.EMAIL_HOST_USER

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=from_email,
        to=[organization_email],
    )
    email.content_subtype = "html" 
    email.send(fail_silently=False)

@shared_task
def send_password_reset_email(user_email):
    """
    Sends a password reset email with a JWT token.
    """
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        raise UserDoesNotExistException(f"User with email {user_email} does not exist.")

    # Generate a JWT token for password reset (valid for 1 hour)
    payload = {
        "user_id": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),  # Use timezone-aware datetime
        "iat": datetime.now(timezone.utc)
    }
    reset_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    reset_link = f"{settings.REACT_FRONTEND_URL}/auth/reset-password/{reset_token}"

    context = {
        "user_name": user.get_full_name if user.get_full_name else user.email,
        "reset_link": reset_link,
    }

    subject = "Reset Your Password"
    html_message = render_to_string("accounts/general/password_reset_email.html", context)
    from_email = settings.EMAIL_HOST_USER

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=from_email,
        to=[user_email],
    )
    email.content_subtype = "html"

    email.send(fail_silently=False)
    return f"Password reset email sent to {user_email}"