from django.utils import timezone
from django.http import HttpRequest

from drf_authentify.models import AuthToken


def delete_request_token(request: HttpRequest) -> None:
    """Remove current tokens associated with authenticated request object"""
    if hasattr(request, "auth"):
        AuthToken.objects.filter(token=request.auth).delete()


def clear_request_tokens(request: HttpRequest) -> None:
    """Remove all tokens associated to user instance from authenticated request object"""
    if hasattr(request, "user"):
        AuthToken.objects.filter(user=request.user).delete()


def clear_user_tokens(user) -> None:
    """Remove all tokens associated to user instance"""
    AuthToken.objects.filter(user=user).delete()


def clear_expired_tokens() -> None:
    """Clears all expired tokens from database"""
    AuthToken.objects.filter(expires_at__lt=timezone.now()).delete()
