import secrets
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model

from drf_authentify.models import AuthToken
from drf_authentify.choices import AUTHTYPE_CHOICES
from drf_authentify.admin import AuthTokenAdmin, ExpirationStatusFilter


class TestExpirationStatusFilter(TestCase):
    def setUp(self):
        now = timezone.now()

        username = "john.doe"
        password = "hunter2"
        email = "john.doe@example.com"
        self.user = get_user_model().objects.create_user(username, email, password)

        self.valid_token = AuthToken.objects.create(
            user=self.user,
            created_at=now,
            token=secrets.token_urlsafe(),
            auth_type=AUTHTYPE_CHOICES.HEADER,
            expires_at=now + timedelta(days=1),
        )

        self.expired_token = AuthToken.objects.create(
            user=self.user,
            created_at=now,
            token=secrets.token_urlsafe(),
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=now - timedelta(days=1),
        )

    def test_filter_valid_tokens(self):
        filter_instance = ExpirationStatusFilter(
            request=None,
            params={"expiration": "valid"},
            model=AuthToken,
            model_admin=AuthTokenAdmin,
        )
        queryset = AuthToken.objects.all()
        filtered_queryset = filter_instance.queryset(None, queryset)

        self.assertIn(self.valid_token, filtered_queryset)
        self.assertNotIn(self.expired_token, filtered_queryset)

    def test_filter_expired_tokens(self):
        filter_instance = ExpirationStatusFilter(
            request=None,
            params={"expiration": "expired"},
            model=AuthToken,
            model_admin=AuthTokenAdmin,
        )
        queryset = AuthToken.objects.all()
        filtered_queryset = filter_instance.queryset(None, queryset)

        self.assertIn(self.expired_token, filtered_queryset)
        self.assertNotIn(self.valid_token, filtered_queryset)

    def test_auth_token_admin(self):
        admin_site = AdminSite()
        admin_instance = AuthTokenAdmin(model=AuthToken, admin_site=admin_site)

        self.assertIn(ExpirationStatusFilter, admin_instance.list_filter)

    def test_valid_method(self):
        now = timezone.now()
        valid_token = AuthToken.objects.create(
            user=self.user,
            created_at=now,
            token=secrets.token_urlsafe(),
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=now + timedelta(days=1),
        )

        expired_token = AuthToken.objects.create(
            user=self.user,
            created_at=now,
            token=secrets.token_urlsafe(),
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=now - timedelta(days=1),
        )

        admin_instance = AuthTokenAdmin(model=AuthToken, admin_site=AdminSite())

        self.assertTrue(admin_instance.valid(valid_token))
        self.assertFalse(admin_instance.valid(expired_token))
