import secrets
import hashlib

from drf_authentify.settings import authentify_settings


def _hash_token(token: str) -> str:
    """Hash a token using the configured secure hash algorithm."""
    algorithm = authentify_settings.SECURE_HASH_ALGORITHM.lower()
    hasher = hashlib.new(algorithm)
    hasher.update(token.encode("utf-8"))
    return hasher.hexdigest()


def _generate_token(nbytes: int) -> tuple[str, str]:
    """Generate a raw token and its hashed form."""
    raw = secrets.token_urlsafe(nbytes)
    return raw, _hash_token(raw)


def generate_access_token() -> tuple[str, str]:
    return _generate_token(32)


def generate_refresh_token() -> tuple[str, str]:
    return _generate_token(48)


def hash_token_string(raw_token: str) -> str:
    return _hash_token(raw_token)
