from datetime import timedelta

from django.utils import timezone
from django.http import HttpRequest
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from drf_authentify.models import AuthToken
from drf_authentify.utils import generate_token
from drf_authentify.choices import AUTHTYPE_CHOICES
from drf_authentify.settings import authentify_settings


class TokenService:
    @staticmethod
    def _generate_token(
        user, auth_type: AUTHTYPE_CHOICES, context: dict = None, expires_in: int = None
    ) -> str:
        """
        Attempt to create a unique token for the user, retrying on rare collisions.
        """
        context = context or {}
        token_duration = expires_in or authentify_settings.TOKEN_EXPIRATION
        expiration = timezone.now() + timedelta(seconds=token_duration)

        for __ in range(authentify_settings.MAX_TOKEN_CREATION_ATTEMPTS):
            token = generate_token()
            try:
                AuthToken.objects.create(
                    user=user,
                    token=token,
                    context=context,
                    auth_type=auth_type,
                    expires_at=expiration,
                )
                return token
            except IntegrityError:
                continue

        raise RuntimeError(_("Failed to generate unique token after multiple attempts"))

    @staticmethod
    def generate_cookie_token(
        user, context: dict = None, expires_in: int = None
    ) -> str:
        """Generate a COOKIE-based auth token."""
        return TokenService._generate_token(
            user, AUTHTYPE_CHOICES.COOKIE, context=context, expires_in=expires_in
        )

    @staticmethod
    def generate_header_token(
        user, context: dict = None, expires_in: int = None
    ) -> str:
        """Generate a HEADER-based auth token."""
        return TokenService._generate_token(
            user, AUTHTYPE_CHOICES.HEADER, context=context, expires_in=expires_in
        )

    @staticmethod
    def verify_token(token: str, auth_type: AUTHTYPE_CHOICES = None) -> AuthToken:
        """Verify a token and optionally match auth_type."""
        filters = {"token": token, "expires_at__gt": timezone.now()}
        if auth_type:
            filters["auth_type"] = auth_type
        return AuthToken.objects.filter(**filters).first()

    @staticmethod
    def revoke_token_from_request(request: HttpRequest) -> None:
        """Delete the token attached to the request."""
        token = getattr(request, "auth", None)
        if isinstance(token, AuthToken):
            token.delete()

    @staticmethod
    def revoke_all_tokens_for_user_from_request(request: HttpRequest) -> None:
        """Delete all tokens for the user associated with the request."""
        user = getattr(request, "user", None)
        TokenService.revoke_all_user_tokens(user)

    @staticmethod
    def revoke_all_user_tokens(user) -> None:
        """Delete all tokens for the given authenticated user."""
        if user and user.is_authenticated:
            AuthToken.objects.filter(user=user).delete()

    @staticmethod
    def revoke_expired_tokens() -> None:
        """Delete all expired tokens."""
        AuthToken.objects.filter(expires_at__lt=timezone.now()).delete()
