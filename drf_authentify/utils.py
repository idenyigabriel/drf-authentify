import secrets
from django.utils.translation import gettext_lazy as _

from drf_authentify.settings import authentify_settings


def generate_token() -> str:
    from drf_authentify.models import AuthToken

    for __ in range(authentify_settings.MAX_TOKEN_CREATION_ATTEMPTS):
        token = secrets.token_urlsafe(32)
        if not AuthToken.objects.filter(token=token).exists():
            return token

    raise RuntimeError(_("Could not generate a unique token after several attempts."))
