from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from drf_authentify.context import ContextParams
from drf_authentify.choices import AUTHTYPE_CHOICES
from drf_authentify.validators import validate_dict


class AuthToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    auth_type = models.CharField(max_length=6, choices=AUTHTYPE_CHOICES.choices)
    context = models.JSONField(default=dict, validators=[validate_dict], blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auth_tokens"
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Auth Tokens"

    def clean(self):
        super().clean()

        if not isinstance(self.context, dict):
            raise ValidationError({"context": "Context must be a dictionary."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.token}: {self.user}"

    @property
    def context_obj(self):
        return ContextParams(self.context)
