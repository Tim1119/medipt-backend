from django.core.exceptions import ValidationError

def validate_organization_acronym(value):
    if len(value) < 2 or len(value) > 15:
        raise ValidationError("Organization acronym must be between 2 and 15 characters.")