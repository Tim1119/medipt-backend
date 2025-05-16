from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from celery.exceptions import MaxRetriesExceededError
import logging
from apps.invites.exceptions import EmailSendingFailedException

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_invitation_to_caregiver(self, email, invitation_token, role, organization_name):
    """
    Sends an email invitation to a caregiver with a tokenized invite URL pointing to the frontend.
    """
    try:
        invite_url = f"{settings.REACT_FRONTEND_URL}/auth/caregiver-accept-invitation/{invitation_token}"

        context = {
            'organization_name': organization_name,
            'invite_url': invite_url,
            'caregiver_role': role,
            'expiry_days': getattr(settings, "INVITATION_EXPIRY_DAYS", 7),
        }

        subject = f"You're invited to join {organization_name}"
        html_message = render_to_string(
            'invites/mails/caregiver_invitation_email.html',
            context
        )

        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        # Create and send the email
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=from_email,
            to=recipient_list,
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

        logger.info(f"Invitation email sent to {email} for role {role} in {organization_name} {invite_url}")

    except Exception as e:
        logger.error(f"Failed to send invitation email to {email}: {str(e)}")
        try:
            self.retry(countdown=60)  # Retry after 60 seconds
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for invitation email to {email}")
            raise EmailSendingFailedException(
                detail=f"Failed to send invitation email to {email} after {self.max_retries} attempts."
            )