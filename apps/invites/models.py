from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Lower
from apps.organizations.models import Organization
from shared.models import TimeStampedUUID
from shared.text_choices import CaregiverTypes
import uuid
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

def default_expires_at():
    """Set default expiry based on settings or 7 days."""
    return timezone.now() + timezone.timedelta(days=getattr(settings, "INVITATION_EXPIRY_DAYS", 7))

class InvitationStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACCEPTED = "ACCEPTED", _("Accepted")
    EXPIRED = "EXPIRED", _("Expired")

class CaregiverInvite(TimeStampedUUID):
    email = models.EmailField()
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="caregiver_invites"
    )
    role = models.CharField(max_length=40, choices=CaregiverTypes.choices)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField(default=default_expires_at)
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_caregiver_invites",
        help_text=_("The user who sent this invitation.")
    )
    resend_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of times the invitation was resent.")
    )

    class Meta:
        verbose_name = _("Caregiver Invitation")
        verbose_name_plural = _("Caregiver Invitations")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                "organization",
                name="unique_invite_per_org"
            )
        ]
        indexes = [
            models.Index(fields=["token"]),  # Optimize token lookups
        ]

    def __str__(self):
        return f"Invite for {self.email} ({self.role}) in {self.organization.name}"

    def is_expired(self):
        """Check if the invite has expired."""
        return timezone.now() > self.expires_at or self.status == InvitationStatus.EXPIRED

    def clean(self):
        """Validate role and ensure email is lowercase."""
        if self.role not in dict(CaregiverTypes.choices):
            raise ValidationError({"role": f"Invalid role: {self.role}"})
        self.email = self.email.lower()

    def save(self, *args, **kwargs):
        """Ensure email is lowercase and validate before saving."""
        self.full_clean()  # Run clean() before saving
        if self.status != InvitationStatus.EXPIRED and self.is_expired():
            self.status = InvitationStatus.EXPIRED
        super().save(*args, **kwargs)