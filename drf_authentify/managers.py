from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.db import models, transaction

from drf_authentify.compat import Self
from drf_authentify.choices import AUTH_TYPES
from drf_authentify.types import GeneratedToken
from drf_authentify.utils import generate_token
from drf_authentify.settings import authentify_settings


class AuthTokenQuerySet(models.QuerySet):
    def active(self) -> Self:
        """Return tokens that have not expired."""
        now = timezone.now()
        return self.filter(Q(expires_at__gt=now) | Q(expires_at__isnull=True))

    def refreshable(self) -> Self:
        """Return tokens that can still be refreshed."""
        return self.filter(
            refresh_token__isnull=False, refresh_until__gt=timezone.now()
        )

    def expired(self) -> Self:
        """Return expired tokens."""
        return self.filter(expires_at__lte=timezone.now())

    def for_user(self, user) -> Self:
        """Filter tokens for a specific user."""
        return self.filter(user=user)

    def delete_expired(self) -> int:
        """Delete all expired tokens and return count."""
        deleted, _ = self.expired().delete()
        return deleted


class AuthTokenManager(models.Manager):
    def get_queryset(self) -> Self:
        return AuthTokenQuerySet(self.model, using=self._db)

    def active(self) -> Self:
        return self.get_queryset().active()

    def refreshable(self) -> Self:
        return self.get_queryset().refreshable()

    def expired(self) -> Self:
        return self.get_queryset().expired()

    def for_user(self, user) -> Self:
        return self.get_queryset().for_user(user)

    def delete_expired(self) -> int:
        return self.get_queryset().delete_expired()

    @transaction.atomic
    def create_token(
        self,
        user,
        auth_type: AUTH_TYPES,
        context: dict = None,
        expires_in: timedelta = None,
    ) -> GeneratedToken:
        # Enforce single login — remove existing active tokens
        if authentify_settings.ENFORCE_SINGLE_LOGIN:
            if authentify_settings.KEEP_EXPIRED_TOKENS:
                now = timezone.now()
                old_date = now - timedelta(days=1)
                self.filter(user=user).update(
                    revoked_at=now, expires_at=old_date, refresh_until=old_date
                )
            else:
                self.filter(user=user).delete()

        now = timezone.now()

        # Compute expiration times
        ttl = expires_in or authentify_settings.TOKEN_TTL
        refresh_ttl = authentify_settings.REFRESH_TOKEN_TTL

        expires_at = now + ttl if ttl else None
        refresh_until = now + refresh_ttl if refresh_ttl else None

        # Generate tokens
        raw_token, hashed_token = generate_token()
        raw_refresh_token, hashed_refresh_token = (None, None)

        token_data = {
            "user": user,
            "token": hashed_token,
            "auth_type": auth_type,
            "context": context or {},
            "expires_at": expires_at,
            "last_refreshed_at": now,
        }

        if refresh_ttl:
            raw_refresh_token, hashed_refresh_token = generate_token()
            token_data.update(
                refresh_until=refresh_until,
                refresh_token=hashed_refresh_token,
            )

        # Create token
        token = self.create(**token_data)
        return GeneratedToken(raw_token, raw_refresh_token, token)
