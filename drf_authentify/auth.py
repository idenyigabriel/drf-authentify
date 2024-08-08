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

                # if auth restriction is enabled, then filter for token with token auth
                if authentify_settings.ENABLE_AUTH_RESTRICTION:
                    token = AuthToken.verify_token(token_str, AUTH.TOKEN)
                else:
                    token = AuthToken.verify_token(token_str)

                if token:
                    return (token.user, token)

        return None

    def authenticate_header(self, request):
        auth = request.META["HTTP_AUTHORIZATION"].split()
        allowed_prefixes = [
            prefix.lower() for prefix in authentify_settings.ALLOWED_HEADER_PREFIXES
        ]

        if not auth or len(auth) != 2 or auth[0].lower() not in allowed_prefixes:
            return None
        return auth[1]


class CookieAuthentication(BaseAuthentication):
    """Simple cookie based authentication."""

    def authenticate(self, request):
        if authentify_settings.COOKIE_KEY in request.COOKIES:
            token_str = request.COOKIES[authentify_settings.COOKIE_KEY]
            if token_str:

                # if auth restriction is enabled, then filter for token with auth
                if authentify_settings.ENABLE_AUTH_RESTRICTION:
                    token = AuthToken.verify_token(token_str, AUTH.COOKIE)
                else:
                    token = AuthToken.verify_token(token_str)

                if token:
                    return (token.user, token)

        return None

    def authenticate_header(self, request):
        return request.COOKIES[authentify_settings.COOKIE_KEY]
