from django.db import models
from django.utils.translation import gettext_lazy as _ 


class UserRoles(models.TextChoices):
    PATIENT = 'Patient', _('Patient')
    CAREGIVER = 'Caregiver', _('Caregiver')
    ORGANIZATION = 'Organization', _('Organization')
    ORGANIZATION_ADMIN = 'Organization_Admin', _('Organization_Admin')


