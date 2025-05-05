import secrets
from datetime import timedelta
from django.utils import timezone
from django.http import HttpRequest

from drf_authentify.choices import AUTHTYPE_CHOICES
from drf_authentify.models import AuthToken
from drf_authentify.settings import authentify_settings


class TokenService:
    @staticmethod
    def _generate_token(
        user, auth_type: AUTHTYPE_CHOICES, context: dict = None, expires_in: int = None
    ) -> str:
        token = secrets.token_urlsafe()
        token_duration = expires_in or authentify_settings.TOKEN_EXPIRATION
        expiration = timezone.now() + timedelta(seconds=token_duration)

        AuthToken.objects.create(
            user=user,
            token=token,
            auth_type=auth_type,
            context=context or {},
            expires_at=expiration,
        )
        return token

    @staticmethod
    def generate_cookie_token(user, context: dict = {}, expires_in: int = None) -> str:
        return TokenService._generate_token(
            user, AUTHTYPE_CHOICES.COOKIE, context=context, expires_in=expires_in
        )

    @staticmethod
    def generate_header_token(user, context: dict = {}, expires_in: int = None) -> str:
        return TokenService._generate_token(
            user, AUTHTYPE_CHOICES.HEADER, context=context, expires_in=expires_in
        )

    @staticmethod
    def verify_token(token: str, auth_type: AUTHTYPE_CHOICES = None) -> AuthToken:
        filters = {"token": token, "expires_at__gt": timezone.now()}
        if auth_type:
            filters["auth_type"] = auth_type
        return AuthToken.objects.filter(**filters).first()

    @staticmethod
    def revoke_token_from_request(request: HttpRequest) -> None:
        token = getattr(request, "auth", None)
        if isinstance(token, AuthToken):
            token.delete()

    @staticmethod
    def revoke_all_tokens_for_user_from_request(request: HttpRequest) -> None:
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            AuthToken.objects.filter(user=user).delete()

    @staticmethod
    def revoke_all_user_tokens(user) -> None:
        if user and user.is_authenticated:
            AuthToken.objects.filter(user=user).delete()

    @staticmethod
    def revoke_expired_tokens() -> None:
        AuthToken.objects.filter(expires_at__lt=timezone.now()).delete()
