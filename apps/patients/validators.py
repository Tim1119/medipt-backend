import re
from django.core.exceptions import ValidationError


def validate_blood_pressure(value):
    if not re.match(r'^\d{2,3}/\d{2,3}$', value):
        raise ValidationError(
            'Enter a valid blood pressure in the format "120/80".'
        )