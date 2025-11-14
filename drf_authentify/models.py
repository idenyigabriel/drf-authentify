from django.apps import apps
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

from drf_authentify.compat import Type
from drf_authentify.choices import AUTH_TYPES
from drf_authentify.contexts import ContextParams
from drf_authentify.validators import validate_dict
from drf_authentify.managers import AuthTokenManager
from drf_authentify.settings import authentify_settings


# Type alias for token model
TokenType = Type["AuthToken"]


def get_token_model() -> TokenType:
    """
    Return the current swappable AuthToken model class.
    Resolves only when called.
    """
    model_path = authentify_settings.TOKEN_MODEL
    if "." in model_path:
        app_label, model_name = model_path.rsplit(".", 1)
        return apps.get_model(app_label, model_name)
    # This path is usually not used for swappable models, but maintained for compatibility
    return import_string(model_path)


class AbstractAuthToken(models.Model):
    token = models.CharField(max_length=255, unique=True, db_index=True)
    refresh_token = models.CharField(
        null=True, blank=True, unique=True, db_index=True, max_length=255
    )
    auth_type = models.CharField(max_length=12, choices=AUTH_TYPES.choices)
    context = models.JSONField(default=dict, blank=True, validators=[validate_dict])
    last_refreshed_at = models.DateTimeField(default=timezone.now)
    refresh_until = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_tokens"
    )

    objects: AuthTokenManager = AuthTokenManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        verbose_name = "Authentication Token"
        verbose_name_plural = "Authentication Tokens"

    def __str__(self):
        return f"{self.user} ({self.auth_type})"

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and timezone.now() >= self.expires_at

    @property
    def context_obj(self) -> ContextParams:
        return ContextParams(self.context)


class AuthToken(AbstractAuthToken):
    class Meta(AbstractAuthToken.Meta):
        swappable = "drf_authentify.AuthToken"
