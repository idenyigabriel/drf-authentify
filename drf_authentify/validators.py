from django.core.exceptions import ValidationError


def validate_dict(value):
    if not isinstance(value, dict):
        raise ValidationError("Context must be a dictionary.")
