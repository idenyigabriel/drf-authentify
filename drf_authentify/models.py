import json
import secrets
from typing import Any
from django.db import models
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from drf_authentify.choices import AUTH
from drf_authentify.settings import authentify_settings


class AuthToken(models.Model):
    token = models.CharField(max_length=255, unique=True, blank=False, null=False)
    auth = models.CharField(max_length=6, choices=AUTH.choices, blank=False, null=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user",
        blank=False,
        null=False,
    )
    _context = models.TextField("context", blank=True, null=True)
    expires_at = models.DateTimeField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.token} : {self.user}"

    @property
    def context(self) -> Any:
        return json.loads(self._context)

    @context.setter
    def context(self, value):
        self._context = json.dumps(value)

    @classmethod
    def __generate_token(
        cls, user, auth, context: Any = None, expires: int = None
    ) -> str:
        """This is utility method for generating authtoken instancest"""
        default_expiration = authentify_settings.TOKEN_EXPIRATION
        expires = timezone.now() + timedelta(seconds=expires or default_expiration)
        token = secrets.token_urlsafe()
        cls.objects.create(
            token=token, user=user, context=context, auth=auth, expires_at=expires
        )
        return token

    @classmethod
    def generate_cookie_token(
        cls, user, context: Any = None, expires: int = None
    ) -> str:
        """Generate cookie type auth token"""
        return cls.__generate_token(user, AUTH.COOKIE, context=context, expires=expires)

    @classmethod
    def generate_header_token(
        cls, user, context: Any = None, expires: int = None
    ) -> str:
        """Generate authorization header type auth token"""
        return cls.__generate_token(user, AUTH.TOKEN, context=context, expires=expires)

    @classmethod
    def verify_token(cls, token: str, auth: AUTH = None) -> object:
        """Verify token validity"""
        now = timezone.now()
        if not auth:
            return cls.objects.filter(token=token, expires_at__gt=now).first()
        return cls.objects.filter(token=token, auth=auth, expires_at__gt=now).first()
