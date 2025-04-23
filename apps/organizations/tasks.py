from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def send_patient_account_creation_notification_email(patient_email, patient_password,patient_full_name, organization_name):

    """
    Sends an email notification to a patient notifying them of their newly created account.
    """
    # Construct the login URL for the frontend
    login_url = f"{settings.REACT_FRONTEND_URL}/login"

    context = {
        'organization_name': organization_name,
        'patient_email': patient_email,
        'patient_full_name': patient_full_name,
        'patient_password': patient_password,
        'login_url': login_url,
    }

    subject = f"Welcome to {organization_name}! Your Patient Account is Ready"
    html_message = render_to_string('organizations/mails/patient_succesful_account_notification_mail.html', context)

    from_email = settings.EMAIL_HOST_USER
    recipient_list = [patient_email]  

    # Create and send the email
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=from_email,
        to=recipient_list,
    )
    email.content_subtype = "html" 
    email.send(fail_silently=False)
