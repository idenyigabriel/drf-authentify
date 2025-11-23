from datetime import timedelta

from django.utils import timezone

from drf_authentify.choices import AUTH_TYPES
from drf_authentify.types import IssuedTokens
from drf_authentify.compat import Union, Optional
from drf_authentify.settings import authentify_settings
from drf_authentify.utils.tokens import hash_token_string
from drf_authentify.models import TokenType, get_token_model


# Get the current token model
AuthToken = get_token_model()


class TokenService:
    @staticmethod
    def _generate_auth_token(
        user,
        auth_type: AUTH_TYPES,
        context: Optional[dict] = None,
        access_expires_in: Optional[timedelta] = None,
        refresh_expires_in: Optional[timedelta] = None,
    ) -> IssuedTokens:
        """
        Generate and return a token and refresh token (if applicable), based on the auth type and expiration settings.
        Accepts expires_in as a timedelta object.
        """
        return AuthToken.objects.create_token(
            user,
            auth_type,
            context=context,
            access_expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in,
        )

    @staticmethod
    def generate_cookie_token(
        user,
        context: Optional[dict] = None,
        access_expires_in: Optional[int] = None,
        refresh_expires_in: Optional[int] = None,
    ) -> IssuedTokens:
        """
        Generate a cookie token with an optional expiration time (in seconds).
        """
        return TokenService._generate_auth_token(
            user,
            AUTH_TYPES.COOKIE,
            context=context,
            access_expires_in=(
                timedelta(seconds=access_expires_in) if access_expires_in else None
            ),
            refresh_expires_in=(
                timedelta(seconds=refresh_expires_in) if refresh_expires_in else None
            ),
        )

    @staticmethod
    def generate_header_token(
        user,
        context: Optional[dict] = None,
        access_expires_in: Optional[int] = None,
        refresh_expires_in: Optional[int] = None,
    ) -> IssuedTokens:
        """
        Generate a header token with an optional expiration time (in seconds).
        """
        return TokenService._generate_auth_token(
            user,
            AUTH_TYPES.HEADER,
            context=context,
            access_expires_in=(
                timedelta(seconds=access_expires_in) if access_expires_in else None
            ),
            refresh_expires_in=(
                timedelta(seconds=refresh_expires_in) if refresh_expires_in else None
            ),
        )

    @staticmethod
    def verify_token(
        token: str, auth_type: AUTH_TYPES = None
    ) -> Union[TokenType, None]:
        """
        Verify if the provided token is valid and not expired.
        """
        hashed_token = hash_token_string(token)
        filters = {"access_token_hash": hashed_token}

        if auth_type:
            filters["auth_type"] = auth_type

        return (
            AuthToken.objects.active().filter(**filters).select_related("user").first()
        )

    @staticmethod
    def revoke_token(token: TokenType) -> None:
        """
        Revoke a single token.
        """
        AuthToken.objects.filter(id=token.id).delete()

    @staticmethod
    def revoke_all_user_tokens(user) -> None:
        """
        Revoke all tokens for a specific user.
        """
        if user and user.is_authenticated:
            AuthToken.objects.filter(user=user).delete()

    @staticmethod
    def revoke_all_expired_user_tokens(user) -> None:
        """
        Revoke all expired tokens for a specific user.
        """
        AuthToken.objects.for_user(user).expired().delete()

    @staticmethod
    def revoke_expired_tokens() -> None:
        """
        Revoke all expired tokens.
        """
        AuthToken.objects.delete_expired()

    @staticmethod
    def refresh_token(
        refresh_token: str,
        access_expires_in: Optional[int] = None,
        refresh_expires_in: Optional[int] = None,
    ) -> Optional[IssuedTokens]:
        """
        Refresh an auth token using a valid refresh token.
        Returns (raw_token, raw_refresh_token, new_token_instance), or None if invalid.
        """
        hashed_refresh = hash_token_string(refresh_token)

        # Find the token with the given refresh token that is still valid
        token = (
            AuthToken.objects.refreshable()
            .filter(refresh_token_hash=hashed_refresh)
            .first()
        )

        if not token:
            return None  # Invalid or expired refresh token

        user = token.user
        context = token.context
        auth_type = token.auth_type

        # Delete old token
        if authentify_settings.KEEP_EXPIRED_TOKENS:
            now = timezone.now()
            old_date = now - timedelta(days=1)
            token.revoked_at = now
            token.expires_at = old_date
            token.refresh_until = old_date
            token.save(update_fields=["revoked_at", "expires_at", "refresh_until"])
        else:
            token.delete()

        # Create new token
        return TokenService._generate_auth_token(
            user,
            auth_type,
            context=context,
            access_expires_in=(
                timedelta(seconds=access_expires_in) if access_expires_in else None
            ),
            refresh_expires_in=(
                timedelta(seconds=refresh_expires_in) if refresh_expires_in else None
            ),
        )
