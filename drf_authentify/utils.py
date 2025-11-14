import secrets
import hashlib

from drf_authentify.settings import authentify_settings


def generate_token() -> tuple[str, str]:
    """
    Generate a random token and hash it using the configured secure hash algorithm.
    """
    raw_token = secrets.token_urlsafe(32)
    hash_algo = authentify_settings.SECURE_HASH_ALGORITHM.lower()
    try:
        hasher = hashlib.new(hash_algo)
    except ValueError:
        raise RuntimeError(
            f"Invalid SECURE_HASH_ALGORITHM '{hash_algo}' in DRF_AUTHENTIFY settings."
        )

    hasher.update(raw_token.encode("utf-8"))
    return raw_token, hasher.hexdigest()


def generate_token_string_hash(raw_token: str) -> str:
    """
    Hash an existing token string using the configured secure hash algorithm.
    """
    hash_algo = authentify_settings.SECURE_HASH_ALGORITHM.lower()
    try:
        hasher = hashlib.new(hash_algo)
    except ValueError:
        raise RuntimeError(
            f"Invalid SECURE_HASH_ALGORITHM '{hash_algo}' in DRF_AUTHENTIFY settings."
        )

    hasher.update(raw_token.encode("utf-8"))
    return hasher.hexdigest()
