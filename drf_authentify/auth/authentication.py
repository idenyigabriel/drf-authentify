from rest_framework.authentication import BaseAuthentication

from drf_authentify.services import TokenService
from drf_authentify.choices import AUTHTYPE_CHOICES
from drf_authentify.settings import authentify_settings


class BaseTokenAuth(BaseAuthentication):
    """
    Base class for token-based authentication.
    Provides shared logic for cookie and header authentication classes.
    """

    source = None  # "header" or "cookie"
    auth_type = None  # AUTHTYPE_CHOICES.HEADER or AUTHTYPE_CHOICES.COOKIE

    def authenticate(self, request):
        token_str = self._get_token_from_request(request)
        if not token_str:
            return None

        if authentify_settings.ENABLE_AUTH_RESTRICTION and self.auth_type:
            token = TokenService.verify_token(token_str, self.auth_type)
        else:
            token = TokenService.verify_token(token_str)

        if token:
            return (token.user, token)
        return None

    def _get_token_from_request(self, request):
        raise NotImplementedError("Must implement _get_token_from_request")

    def authenticate_header(self, request):
        return f'{self.source}="api"'


class AuthorizationHeaderAuthentication(BaseTokenAuth):
    """
    Token-based authentication via Authorization headers.
    Example: Authorization: Token <token>
    """

    source = "Authorization header"
    auth_type = AUTHTYPE_CHOICES.HEADER

    def _get_token_from_request(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        parts = header.split()

        if len(parts) == 2:
            prefix, token = parts
            allowed_prefixes = [
                p.lower() for p in authentify_settings.ALLOWED_HEADER_PREFIXES
            ]
            if prefix.lower() in allowed_prefixes:
                return token
        return None


class CookieAuthentication(BaseTokenAuth):
    """
    Token-based authentication via cookie.
    Example: Cookie: token=<token>
    """

    source = "HTTP cookie"
    auth_type = AUTHTYPE_CHOICES.COOKIE

    def _get_token_from_request(self, request):
        return request.COOKIES.get(authentify_settings.COOKIE_KEY)
