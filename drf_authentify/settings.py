from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings


USER_SETTINGS = getattr(settings, "DRF_AUTHENTIFY", None)

DEFAULTS = {
    "ALLOWED_HEADER_PREFIXES": ["bearer", "token"],
    "TOKEN_EXPIRATION": 3000,
    "COOKIE_KEY": "token",
}

authentify_settings = APISettings(USER_SETTINGS, DEFAULTS)


def reload_api_settings(*args, **kwargs):
    global authentify_settings
    setting, value = kwargs["setting"], kwargs["value"]
    if setting == "DRF_AUTHENTIFY":
        authentify_settings = APISettings(value, DEFAULTS, {})


setting_changed.connect(reload_api_settings)
