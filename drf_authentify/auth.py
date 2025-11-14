from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured

from drf_authentify.choices import AUTH_TYPES
from drf_authentify.services import TokenService
from drf_authentify.settings import authentify_settings


class BaseTokenAuth(BaseAuthentication):
    source = None
    auth_type = None

    def authenticate(self, request):
        token_str = self._get_token_from_request(request)
        if not token_str:
            return None

        # Verify token
        token = TokenService.verify_token(
            token_str,
            self.auth_type if authentify_settings.ENFORCE_SINGLE_LOGIN else None,
        )

        if not token:
            return None

        # Reject inactive users
        if not token.user.is_active:
            raise AuthenticationFailed(_("User account is inactive or deleted."))

        self._handle_auto_refresh(token)
        self.run_post_auth_handler(token.user, token)
        return (token.user, token)

    def _handle_auto_refresh(self, token):
        if not getattr(authentify_settings, "AUTO_REFRESH", False):
            return

        refresh_interval = authentify_settings.AUTO_REFRESH_INTERVAL
        if not refresh_interval:
            return  # min interval not reached

        elapsed = timezone.now() - token.last_refreshed_at
        if elapsed < refresh_interval:
            return  # min TTL not reached, skip refresh

        max_ttl = authentify_settings.AUTO_REFRESH_MAX_TTL
        if max_ttl and (timezone.now() - token.created_at) > max_ttl:
            return  # max TTL exceeded

        TokenService.extend_token(token)

    def _get_token_from_request(self, request):
        raise NotImplementedError("Subclasses must implement _get_token_from_request")

    def authenticate_header(self, request):
        if self.source == "Authorization header":
            return 'Authorization realm="api"'
        if self.source == "HTTP cookie":
            return 'Cookie realm="api"'
        return None

    def run_post_auth_handler(self, user, token):
        handler_path = getattr(authentify_settings, "POST_AUTH_HANDLER", None)
        if not handler_path:
            return

        try:
            handler = import_string(handler_path)
        except ImportError as e:
            raise ImproperlyConfigured(
                f"DRF_AUTHENTIFY['POST_AUTH_HANDLER'] is set to '{handler_path}' "
                f"but could not be imported: {e}"
            )

        if not callable(handler):
            raise ImproperlyConfigured(
                f"DRF_AUTHENTIFY['POST_AUTH_HANDLER'] must be callable. "
                f"Got {type(handler).__name__}."
            )

        handler(user=user, token=token)


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
