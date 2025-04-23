import re,uuid
from django.core.exceptions import ValidationError

def validate_phone_number(value):
    nigerian_phone_regex = re.compile(r'^(?:\+234|0)[789]\d{9}$')

    if not nigerian_phone_regex.match(value):
        raise ValidationError(
            'Enter a valid Nigerian phone number. It should start with +234 or 0 and contain 10 digits.'
        )
    
def validate_uuid(id, version=None):
    try:
        uuid_str = str(id)
        uuid_obj = uuid.UUID(uuid_str)
        if version is not None:
            return uuid_obj.version == version
        return True
    except (ValueError, AttributeError, TypeError):
        return False