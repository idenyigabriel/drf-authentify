from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.db import models, transaction

from drf_authentify.compat import Self
from drf_authentify.compat import Optional
from drf_authentify.choices import AUTH_TYPES
from drf_authentify.types import IssuedTokens
from drf_authentify.settings import authentify_settings
from drf_authentify.utils.tokens import generate_access_token, generate_refresh_token


class AuthTokenQuerySet(models.QuerySet):
    def active(self) -> Self:
        """Return tokens that have not expired."""
        now = timezone.now()
        return self.filter(Q(expires_at__gt=now) | Q(expires_at__isnull=True))

    def refreshable(self) -> Self:
        """Return tokens that can still be refreshed."""
        return self.filter(
            refresh_token_hash__isnull=False, refresh_until__gt=timezone.now()
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
        context: Optional[dict] = None,
        access_expires_in: Optional[timedelta] = None,
        refresh_expires_in: Optional[timedelta] = None,
    ) -> IssuedTokens:
        now = timezone.now()
        context = context or {}

        # Single-login enforcement
        if authentify_settings.ENFORCE_SINGLE_LOGIN:
            qs = self.filter(user=user)
            if authentify_settings.KEEP_EXPIRED_TOKENS:
                old_date = now - timedelta(days=1)
                qs.update(revoked_at=now, expires_at=old_date, refresh_until=old_date)
            else:
                qs.delete()

        # Compute expiration times
        ttl = access_expires_in or authentify_settings.TOKEN_TTL
        refresh_ttl = refresh_expires_in or authentify_settings.REFRESH_TOKEN_TTL

        expires_at = now + ttl if ttl else None
        refresh_until = now + refresh_ttl if refresh_ttl else None

        # Generate tokens
        raw_token, hashed_token = generate_access_token()
        raw_refresh_token, hashed_refresh_token = (None, None)

        token_data = {
            "user": user,
            "context": context,
            "auth_type": auth_type,
            "expires_at": expires_at,
            "last_refreshed_at": now,
            "access_token_hash": hashed_token,
        }

        if refresh_ttl is not None:
            raw_refresh_token, hashed_refresh_token = generate_refresh_token()
            token_data.update(
                refresh_until=refresh_until,
                refresh_token_hash=hashed_refresh_token,
            )

        # Create token
        token = self.create(**token_data)
        return IssuedTokens(raw_token, raw_refresh_token, token)
