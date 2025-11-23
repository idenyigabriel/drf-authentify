import hashlib
from datetime import timedelta
from rest_framework.settings import APISettings

from django.conf import settings
from django.test.signals import setting_changed
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured


DEFAULTS = {
    "TOKEN_TTL": timedelta(hours=24),
    "REFRESH_TOKEN_TTL": timedelta(days=7),
    "AUTO_REFRESH": False,
    "AUTO_REFRESH_MAX_TTL": None,
    "AUTO_REFRESH_INTERVAL": None,
    "TOKEN_MODEL": "drf_authentify.AuthToken",
    "AUTH_COOKIE_NAMES": ["token"],
    "AUTH_HEADER_PREFIXES": ["Bearer", "Token"],
    "SECURE_HASH_ALGORITHM": "sha256",
    "ENFORCE_SINGLE_LOGIN": False,
    "STRICT_CONTEXT_ACCESS": False,
    "ENABLE_AUTH_RESTRICTION": True,
    "KEEP_EXPIRED_TOKENS": False,
    "POST_AUTH_HANDLER": None,
    "POST_AUTO_REFRESH_HANDLER": None,
}

EXPECTED_TYPES = {
    "TOKEN_TTL": (timedelta, type(None)),
    "REFRESH_TOKEN_TTL": (timedelta, type(None)),
    "AUTO_REFRESH": bool,
    "AUTO_REFRESH_MAX_TTL": (timedelta, type(None)),
    "AUTO_REFRESH_INTERVAL": (timedelta, type(None)),
    "TOKEN_MODEL": str,
    "AUTH_COOKIE_NAMES": list,
    "AUTH_HEADER_PREFIXES": list,
    "SECURE_HASH_ALGORITHM": str,
    "ENFORCE_SINGLE_LOGIN": bool,
    "STRICT_CONTEXT_ACCESS": bool,
    "ENABLE_AUTH_RESTRICTION": bool,
    "KEEP_EXPIRED_TOKENS": bool,
    "POST_AUTH_HANDLER": (str, type(None)),
    "POST_AUTO_REFRESH_HANDLER": (str, type(None)),
}


USER_SETTINGS = getattr(settings, "DRF_AUTHENTIFY", None)
authentify_settings = APISettings(USER_SETTINGS, DEFAULTS)


def validate_authentify_settings():
    for key, expected_type in EXPECTED_TYPES.items():
        value = getattr(authentify_settings, key, None)

        # 1 Type validation
        if not isinstance(value, expected_type):
            raise ImproperlyConfigured(
                _(
                    f"Invalid type for DRF_AUTHENTIFY setting '{key}': "
                    f"expected {expected_type}, got {type(value).__name__}"
                )
            )

        # 2 List of strings validation
        if key in ("AUTH_COOKIE_NAMES", "AUTH_HEADER_PREFIXES"):
            if len(value) == 0:
                raise ImproperlyConfigured(
                    f"DRF_AUTHENTIFY setting {key} cannot be an empty list."
                )
            if not all(isinstance(v, str) for v in value):
                raise ImproperlyConfigured(
                    _(f"All items in DRF_AUTHENTIFY setting '{key}' must be strings.")
                )

        # 3 Validate hashlib algorithm
        if key == "SECURE_HASH_ALGORITHM" and value not in hashlib.algorithms_available:
            raise ImproperlyConfigured(
                _(
                    f"DRF_AUTHENTIFY setting '{key}' must be a valid hashlib algorithm. "
                    f"'{value}' is not found in hashlib."
                )
            )

        # Timedelta validation
        if (
            key
            in (
                "TOKEN_TTL",
                "REFRESH_TOKEN_TTL",
                "AUTO_REFRESH_MAX_TTL",
                "AUTO_REFRESH_INTERVAL",
            )
            and value is not None
        ):
            if key != "AUTO_REFRESH_INTERVAL" and value <= timedelta(seconds=0):
                raise ImproperlyConfigured(
                    _(f"DRF_AUTHENTIFY setting '{key}' must be positive.")
                )
            if key == "AUTO_REFRESH_INTERVAL" and value < timedelta(seconds=0):
                raise ImproperlyConfigured(
                    _(
                        f"DRF_AUTHENTIFY setting '{key}' cannot be negative; use 0 for refresh on every request."
                    )
                )

    # Logical validations
    token_ttl = authentify_settings.TOKEN_TTL
    auto_refresh = authentify_settings.AUTO_REFRESH
    refresh_ttl = authentify_settings.REFRESH_TOKEN_TTL
    auto_max_ttl = authentify_settings.AUTO_REFRESH_MAX_TTL
    auto_interval = authentify_settings.AUTO_REFRESH_INTERVAL

    if token_ttl and refresh_ttl and refresh_ttl <= token_ttl:
        raise ImproperlyConfigured(
            _(
                "DRF_AUTHENTIFY setting REFRESH_TOKEN_TTL must be strictly greater than TOKEN_TTL."
            )
        )

    if auto_refresh:
        missing = []
        if not refresh_ttl:
            missing.append("REFRESH_TOKEN_TTL")
        if not auto_max_ttl:
            missing.append("AUTO_REFRESH_MAX_TTL")
        if not auto_interval:
            missing.append("AUTO_REFRESH_INTERVAL")
        if missing:
            raise ImproperlyConfigured(
                _(
                    f"DRF_AUTHENTIFY setting AUTO_REFRESH cannot be enabled without the following: {', '.join(missing)}"
                )
            )


def reload_authentify_settings(*args, **kwargs):
    global authentify_settings
    if kwargs["setting"] == "DRF_AUTHENTIFY":
        authentify_settings = APISettings(kwargs["value"], DEFAULTS)
        validate_authentify_settings()


setting_changed.connect(reload_authentify_settings)
validate_authentify_settings()
