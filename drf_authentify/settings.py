import hashlib
from datetime import timedelta
from rest_framework.settings import APISettings

from django.conf import settings
from django.test.signals import setting_changed
from django.core.exceptions import ImproperlyConfigured


DEFAULTS = {
    "TOKEN_TTL": timedelta(hours=1),
    "REFRESH_TOKEN_TTL": timedelta(days=7),
    "AUTO_REFRESH": False,
    "AUTO_REFRESH_MAX_TTL": timedelta(days=30),
    "AUTO_REFRESH_INTERVAL": timedelta(minutes=10),
    "TOKEN_MODEL": "drf_authentify.AuthToken",
    "AUTH_COOKIE_NAMES": ["auth_token"],
    "AUTH_HEADER_PREFIXES": ["Bearer", "Token"],
    "SECURE_HASH_ALGORITHM": "sha256",
    "ENFORCE_SINGLE_LOGIN": False,
    "STRICT_CONTEXT_ACCESS": False,
    "ENABLE_AUTH_RESTRICTION": True,
    "POST_AUTH_HANDLER": None,
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
    "POST_AUTH_HANDLER": (str, type(None)),
}


USER_SETTINGS = getattr(settings, "DRF_AUTHENTIFY", None)
authentify_settings = APISettings(USER_SETTINGS, DEFAULTS)


def validate_authentify_settings():
    """
    Validate user-provided DRF_AUTHENTIFY settings.
    Checks types, list contents, importable paths, valid hash algorithm,
    and callable paths.
    """
    for key, expected_type in EXPECTED_TYPES.items():
        value = getattr(authentify_settings, key, None)

        # 1 Type validation
        if not isinstance(value, expected_type):
            raise ImproperlyConfigured(
                f"Invalid type for DRF_AUTHENTIFY['{key}']: "
                f"expected {expected_type}, got {type(value).__name__}"
            )

        # 2 List of strings validation
        if key in ("AUTH_COOKIE_NAMES", "AUTH_HEADER_PREFIXES"):
            if not all(isinstance(v, str) for v in value):
                raise ImproperlyConfigured(
                    f"All items in DRF_AUTHENTIFY['{key}'] must be strings."
                )

        # 3 Validate hashlib algorithm
        if key == "SECURE_HASH_ALGORITHM" and value not in hashlib.algorithms_available:
            raise ImproperlyConfigured(
                f"DRF_AUTHENTIFY['SECURE_HASH_ALGORITHM'] must be a valid hashlib algorithm. "
                f"'{value}' is not found in hashlib."
            )

        # 4 Validate TimeDelta values (must be positive if set)
        if (
            key
            in (
                "TOKEN_TTL",
                "REFRESH_TOKEN_TTL",
                "AUTO_REFRESH_MAX_TTL",
                "AUTO_REFRESH_INTERVAL",
            )
            and value is not None
            and isinstance(value, timedelta)
        ):
            # AUTO_REFRESH_INTERVAL can be 0 (refresh on every use)
            if key != "AUTO_REFRESH_INTERVAL" and value <= timedelta(seconds=0):
                raise ImproperlyConfigured(
                    f"DRF_AUTHENTIFY['{key}'] must be a positive timedelta."
                )

        # 7 Validate custom token model
        if key == "TOKEN_MODEL" and value is not None:
            if not isinstance(value, str) or "." not in value:
                raise ImproperlyConfigured(
                    "DRF_AUTHENTIFY['TOKEN_MODEL'] must be a valid model path string."
                )

    # Cross-Key Logical Validation (Runs after all keys are loaded)
    token_ttl = authentify_settings.TOKEN_TTL
    refresh_ttl = authentify_settings.REFRESH_TOKEN_TTL
    max_ttl = authentify_settings.AUTO_REFRESH_MAX_TTL

    # --- Logical TTL Checks (None = Infinite) ---

    # 1. Refresh Token TTL must be greater than Access Token TTL (if both are finite)
    if token_ttl is not None and refresh_ttl is not None and refresh_ttl <= token_ttl:
        raise ImproperlyConfigured(
            "DRF_AUTHENTIFY Error: REFRESH_TOKEN_TTL must be strictly greater than TOKEN_TTL (if both are finite)."
        )

    # 2. AUTO_REFRESH_MAX_TTL must not be finite if REFRESH_TOKEN_TTL is infinite
    if max_ttl is not None and refresh_ttl is None:
        raise ImproperlyConfigured(
            "DRF_AUTHENTIFY Error: AUTO_REFRESH_MAX_TTL cannot be set to a finite value if REFRESH_TOKEN_TTL is infinite (None)."
        )

    # 3. AUTO_REFRESH_MAX_TTL must be greater than or equal to REFRESH_TOKEN_TTL (if both are finite)
    if max_ttl is not None and refresh_ttl is not None and max_ttl < refresh_ttl:
        raise ImproperlyConfigured(
            "DRF_AUTHENTIFY Error: AUTO_REFRESH_MAX_TTL must be greater than or equal to REFRESH_TOKEN_TTL."
        )


def reload_authentify_settings(*args, **kwargs):
    global authentify_settings
    if kwargs["setting"] == "DRF_AUTHENTIFY":
        authentify_settings = APISettings(kwargs["value"], DEFAULTS)
        validate_authentify_settings()


setting_changed.connect(reload_authentify_settings)
validate_authentify_settings()
