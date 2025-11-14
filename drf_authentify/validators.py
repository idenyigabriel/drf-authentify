from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_dict(value):
    if not isinstance(value, dict):
        raise ValidationError(_("Context must be a dictionary."))
