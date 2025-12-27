from django.db import models
from django.conf import settings
from django.utils import timezone

from drf_authentify.choices import AUTH_TYPES
from drf_authentify.contexts import ContextParams
from drf_authentify.managers import AuthTokenManager
from drf_authentify.validators import validate_context


# Type alias for token model
class AbstractAuthToken(models.Model):
    access_token_hash = models.CharField(max_length=255, unique=True, db_index=True)
    refresh_token_hash = models.CharField(
        null=True, blank=True, unique=True, db_index=True, max_length=255
    )
    auth_type = models.CharField(max_length=12, choices=AUTH_TYPES.choices)
    context = models.JSONField(default=dict, blank=True, validators=[validate_context])
    last_refreshed_at = models.DateTimeField(default=timezone.now)
    refresh_until = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_index=True,
        on_delete=models.CASCADE,
        related_name="+",
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
