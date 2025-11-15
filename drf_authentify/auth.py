import inspect
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
            self.auth_type if authentify_settings.ENABLE_AUTH_RESTRICTION else None,
        )

        if not token:
            return None

        # Reject inactive users
        if not token.user.is_active:
            raise AuthenticationFailed(_("User account is inactive or deleted."))

        self._handle_auto_refresh(token.user, token, token_str)
        self.run_post_auth_handler(token.user, token, token_str)
        return (token.user, token)

    def _handle_auto_refresh(self, user, token, token_str):
        if not authentify_settings.AUTO_REFRESH:
            return

        elapsed = timezone.now() - token.last_refreshed_at
        if elapsed < authentify_settings.AUTO_REFRESH_INTERVAL:
            return  # min TTL not reached, skip refresh

        now = timezone.now()
        new_expiry = now + authentify_settings.TOKEN_TTL
        max_expiry = token.created_at + authentify_settings.AUTO_REFRESH_MAX_TTL

        if new_expiry > max_expiry:
            return  # max auto refresh TTL exceeded

        token.last_refreshed_at = now
        token.expires_at = new_expiry
        token.refresh_until = now + authentify_settings.REFRESH_TOKEN_TTL
        token.save(update_fields=["expires_at", "refresh_until", "last_refreshed_at"])

        if handler_path := authentify_settings.POST_AUTO_REFRESH_HANDLER:
            try:
                handler = import_string(handler_path)
            except ImportError as e:
                raise ImproperlyConfigured(
                    f"DRF_AUTHENTIFY['POST_AUTO_REFRESH_HANDLER'] is set to '{handler_path}' "
                    f"but could not be imported: {e}"
                )

            if not callable(handler):
                raise ImproperlyConfigured(
                    f"DRF_AUTHENTIFY['POST_AUTO_REFRESH_HANDLER'] must be callable. "
                    f"Got {type(handler).__name__}."
                )

            # Fast argument check
            sig = inspect.signature(handler)
            if len(sig.parameters) != 3:
                raise ImproperlyConfigured(
                    f"DRF_AUTHENTIFY['POST_AUTO_REFRESH_HANDLER'] must accept exactly 3 arguments: "
                    f"user, token and token_str. Found {len(sig.parameters)}."
                )
            return handler(user, token, token_str)
        return user, token

    def _get_token_from_request(self, request):
        raise NotImplementedError("Subclasses must implement _get_token_from_request")

    def authenticate_header(self, request):
        if self.source == "Authorization header":
            return 'Authorization realm="api"'
        if self.source == "HTTP cookie":
            return 'Cookie realm="api"'
        return None

    def run_post_auth_handler(self, user, token, token_str):
        handler_path = authentify_settings.POST_AUTH_HANDLER
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

        # Fast argument check
        sig = inspect.signature(handler)
        if len(sig.parameters) != 3:
            raise ImproperlyConfigured(
                f"DRF_AUTHENTIFY['POST_AUTH_HANDLER'] must accept exactly 3 arguments: "
                f"user, token and token_str. Found {len(sig.parameters)}."
            )

        return handler(user=user, token=token, token_str=token_str)


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
