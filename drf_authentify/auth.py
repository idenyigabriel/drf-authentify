from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

from drf_authentify.choices import AUTH
from drf_authentify.models import AuthToken
from drf_authentify.settings import authentify_settings


class TokenAuthentication(BaseAuthentication):
    """Simple token based authentication."""

    def authenticate(self, request):
        if "HTTP_AUTHORIZATION" in request.META:
            token_str = self.authenticate_header(request)
            if token_str:
                token = AuthToken.verify_token(token_str, AUTH.TOKEN)
                if token:
                    return (token.user, token)
            raise AuthenticationFailed()
        return None

    def get_request_token(self, request):
        auth = request.META["HTTP_AUTHORIZATION"].split()
        allowed_prefixes = [
            prefix.lower() for prefix in authentify_settings.ALLOWED_HEADER_PREFIXES
        ]

        if not auth or len(auth) != 2 or auth[0].lower() in allowed_prefixes:
            return None
        return auth[1]

    def authenticate_header(self, request):
        return request.auth[0].capitalize()


class CookieAuthentication(BaseAuthentication):
    """Simple cookie based authentication."""

    def authenticate(self, request):
        if authentify_settings.COOKIE_KEY in request.COOKIES:
            token_str = request.COOKIES[authentify_settings.COOKIE_KEY]
            if token_str:
                token = AuthToken.verify_token(token_str, AUTH.COOKIE)
                if token:
                    return (token.user, token)
            raise AuthenticationFailed()
        return None

    def authenticate_header(self, request):
        return "Set-Cookie: token=value"
