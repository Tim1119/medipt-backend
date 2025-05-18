from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_patient_account_creation_notification_email(self, patient_email, patient_full_name, organization_name, patient_id):
    """
    Sends a welcome email to a patient after their account is successfully created.
    """
    try:
        login_url = f"{settings.REACT_FRONTEND_URL}/auth/login"

        context = {
            'organization_name': organization_name,
            'patient_email': patient_email,
            'patient_full_name': patient_full_name,
            'login_url': login_url,
        }

        subject = f"Welcome to {organization_name}, {patient_full_name}!"
        html_message = render_to_string('patients/mails/patient_welcome_mail.html', context)

        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[patient_email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

    except Exception as e:
        logger.error(f"Failed to send welcome email to {patient_email}: {str(e)}")
        self.retry(countdown=60, exc=e)