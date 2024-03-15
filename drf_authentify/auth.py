from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

from drf_authentify.choices import AUTH
from drf_authentify.models import AuthToken


class TokenAuthentication(BaseAuthentication):
    """Simple token based authentication."""

    def authenticate(self, request):
        if "HTTP_AUTHORIZATION" in request.META:
            if token := self.get_request_token(request):
                if user := AuthToken.verify_token(token, AUTH.TOKEN):
                    return (user, token)
            raise AuthenticationFailed()
        return None

    def get_request_token(self, request):
        auth = request.META["HTTP_AUTHORIZATION"].split()

        allowed_prefixes = settings.AUTHENTIFY_ALLOWED_HEADER_PREFIXES
        allowed_prefixes = [prefix.lower() for prefix in allowed_prefixes]

        if not auth or len(auth) != 2 or auth[0].lower() in allowed_prefixes:
            return None
        return auth[1]

    def authenticate_header(self, request):
        return request.auth[0].capitalize()


class CookieAuthentication(BaseAuthentication):
    """Simple cookie based authentication."""

    def authenticate(self, request):
        if settings.AUTHENTIFY_COOKIE_KEY in request.COOKIES:
            token = request.COOKIES[settings.AUTHENTIFY_COOKIE_KEY]
            if user := AuthToken.verify_token(token, AUTH.COOKIE):
                return (user, token)
            raise AuthenticationFailed()
        return None

    def authenticate_header(self, request):
        return "Set-Cookie: token=value"
