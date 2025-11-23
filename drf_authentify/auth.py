from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_authentify.choices import AUTH_TYPES
from drf_authentify.services import TokenService
from drf_authentify.utils.imports import load_handler
from drf_authentify.settings import authentify_settings


class BaseTokenAuth(BaseAuthentication):
    source = None
    auth_type = None

    def authenticate(self, request):
        token_str = self._get_token_from_request(request)
        if not token_str:
            return None

        # Verify token
        auth_type = (
            self.auth_type if authentify_settings.ENABLE_AUTH_RESTRICTION else None
        )
        token = TokenService.verify_token(token_str, auth_type)
        if not token:
            return None

        if not token.user.is_active:
            raise AuthenticationFailed(_("User account is inactive or deleted."))

        user, token = self._handle_auto_refresh(token.user, token, token_str)
        user, token = self._run_post_auth_handler(user, token, token_str)
        return (user, token)

    def _handle_auto_refresh(self, user, token, token_str):
        if not authentify_settings.AUTO_REFRESH:
            return user, token

        now = timezone.now()
        elapsed = now - token.last_refreshed_at
        if elapsed < authentify_settings.AUTO_REFRESH_INTERVAL:
            return user, token

        new_expiry = now + authentify_settings.TOKEN_TTL
        max_expiry = token.created_at + authentify_settings.AUTO_REFRESH_MAX_TTL
        if new_expiry > max_expiry:
            return user, token

        token.last_refreshed_at = now
        token.expires_at = new_expiry
        token.refresh_until = now + authentify_settings.REFRESH_TOKEN_TTL
        token.save(update_fields=["expires_at", "refresh_until", "last_refreshed_at"])

        handler = load_handler(
            authentify_settings.POST_AUTO_REFRESH_HANDLER,
            "POST_AUTO_REFRESH_HANDLER",
            ["user", "token", "token_str"],
        )
        if handler:
            return handler(user, token, token_str)
        return user, token

    def _get_token_from_request(self, request):
        raise NotImplementedError("Subclasses must implement _get_token_from_request")

    def authenticate_header(self, request):
        if self.source == "Authorization header":
            prefix = (
                authentify_settings.AUTH_HEADER_PREFIXES[0]
                if authentify_settings.AUTH_HEADER_PREFIXES
                else "Token"
            )
            return f'{prefix} realm="api"'
        if self.source == "HTTP cookie":
            return 'Cookie realm="api"'
        return None

    def _run_post_auth_handler(self, user, token, token_str):
        handler = load_handler(
            authentify_settings.POST_AUTH_HANDLER,
            "POST_AUTH_HANDLER",
            ["user", "token", "token_str"],
        )
        if handler:
            return handler(user=user, token=token, token_str=token_str)
        return user, token


class AuthorizationHeaderAuthentication(BaseTokenAuth):
    source = "Authorization header"
    auth_type = AUTH_TYPES.HEADER

    def _get_token_from_request(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2:
            raise AuthenticationFailed(
                _("Authorization header must be in format: <prefix> <token>.")
            )

        prefix, token = parts
        if prefix not in authentify_settings.AUTH_HEADER_PREFIXES:
            raise AuthenticationFailed(_("Invalid authorization header prefix."))

        return token


class CookieAuthentication(BaseTokenAuth):
    source = "HTTP cookie"
    auth_type = AUTH_TYPES.COOKIE

    def _get_token_from_request(self, request):
        for name in authentify_settings.AUTH_COOKIE_NAMES:
            token = request.COOKIES.get(name)
            if token:
                return token
        return None
