import secrets
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from drf_authentify.models import AuthToken
from drf_authentify.context import ContextParams
from drf_authentify.choices import AUTHTYPE_CHOICES


class AuthTokenModelTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = get_user_model().objects.create_user(
            username="john.doe", email="john.doe@example.com", password="testpassword"
        )

    def test_create_header_auth_token(self):
        token_str = secrets.token_urlsafe()
        token = AuthToken.objects.create(
            user=self.user,
            token=token_str,
            auth_type=AUTHTYPE_CHOICES.HEADER,
            expires_at=self.now + timezone.timedelta(hours=1),
        )

        self.assertEqual(token.context, {})
        self.assertIsNotNone(token.created_at)
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token, token_str)
        self.assertEqual(token.auth_type, AUTHTYPE_CHOICES.HEADER)
        self.assertEqual(token.expires_at, self.now + timezone.timedelta(hours=1))

    def test_create_cookie_auth_token(self):
        token_str = secrets.token_urlsafe()
        token = AuthToken.objects.create(
            user=self.user,
            token=token_str,
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=self.now + timezone.timedelta(hours=1),
        )

        self.assertEqual(token.context, {})
        self.assertIsNotNone(token.created_at)
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token, token_str)
        self.assertEqual(token.auth_type, AUTHTYPE_CHOICES.COOKIE)
        self.assertEqual(token.expires_at, self.now + timezone.timedelta(hours=1))

    def test_create_auth_token_with_context(self):
        context_data = {"device": "mobile", "ip_address": "127.0.0.1"}
        token = AuthToken.objects.create(
            user=self.user,
            context=context_data,
            token="test_token_456",
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=self.now + timezone.timedelta(days=1),
        )
        self.assertEqual(token.context, context_data)
        self.assertIsInstance(token.context_obj, ContextParams)
        self.assertEqual(token.context_obj.device, "mobile")
        self.assertEqual(token.context_obj.ip_address, "127.0.0.1")

    def test_auth_token_unique_token(self):
        AuthToken.objects.create(
            user=self.user,
            token="unique_token",
            auth_type=AUTHTYPE_CHOICES.HEADER,
            expires_at=self.now + timezone.timedelta(hours=2),
        )
        with self.assertRaises(Exception) as context:
            AuthToken.objects.create(
                token="unique_token",
                auth_type=AUTHTYPE_CHOICES.COOKIE,
                user=self.user,
                expires_at=self.now + timezone.timedelta(days=2),
            )
        self.assertIn(
            "Auth token with this Token already exists.", str(context.exception)
        )

    def test_auth_token_auth_type_choices(self):
        valid_auth_types = [choice.value for choice in AUTHTYPE_CHOICES]
        for auth_type in valid_auth_types:
            AuthToken.objects.create(
                user=self.user,
                auth_type=auth_type,
                token=f"test_type_{auth_type}",
                expires_at=self.now + timezone.timedelta(minutes=30),
            )
        with self.assertRaises(ValidationError) as context:
            AuthToken.objects.create(
                user=self.user,
                auth_type="invalid",
                token="invalid_type",
                expires_at=self.now + timezone.timedelta(hours=3),
            )
        self.assertIn("'invalid' is not a valid choice.", str(context.exception))

    def test_auth_token_foreign_key_user(self):
        token = AuthToken.objects.create(
            user=self.user,
            token="user_token",
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=self.now + timezone.timedelta(hours=4),
        )

        self.assertEqual(token.user, self.user)

        token.user.delete()

        with self.assertRaises(AuthToken.DoesNotExist):
            AuthToken.objects.get(pk=token.pk)

    def test_auth_token_ordering(self):
        now = timezone.now()
        token1 = AuthToken.objects.create(
            user=self.user,
            token="token_ordered_1",
            auth_type=AUTHTYPE_CHOICES.HEADER,
            expires_at=now + timezone.timedelta(minutes=10),
        )
        token2 = AuthToken.objects.create(
            user=self.user,
            token="token_ordered_2",
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=now + timezone.timedelta(minutes=20),
        )

        tokens = list(AuthToken.objects.all())
        self.assertEqual(tokens[0], token2)
        self.assertEqual(tokens[1], token1)

    def test_auth_token_verbose_name_plural(self):
        self.assertEqual(str(AuthToken._meta.verbose_name_plural), "Auth Tokens")

    def test_auth_token_clean_method_valid_context(self):
        token = AuthToken(
            user=self.user,
            context={"key": "value"},
            token="valid_context_token",
            auth_type=AUTHTYPE_CHOICES.HEADER,
            expires_at=self.now + timezone.timedelta(hours=5),
        )

        try:
            token.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError for a valid context dictionary.")

    def test_auth_token_clean_method_invalid_context(self):
        token = AuthToken(
            user=self.user,
            context="not a dictionary",
            token="invalid_context_token",
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=self.now + timezone.timedelta(days=3),
        )
        with self.assertRaises(ValidationError) as context:
            token.clean()
        self.assertIn(
            "Context must be a dictionary.", context.exception.message_dict["context"]
        )

    def test_auth_token_string_representation(self):
        token = AuthToken.objects.create(
            user=self.user,
            token="string_token",
            auth_type=AUTHTYPE_CHOICES.HEADER,
            expires_at=self.now + timezone.timedelta(hours=6),
        )
        self.assertEqual(str(token), f"string_token: {self.user}")

    def test_auth_token_context_obj_property(self):
        context_data = {"role": "editor", "permissions": ["read", "write"]}
        token = AuthToken.objects.create(
            user=self.user,
            context=context_data,
            token="context_obj_token",
            auth_type=AUTHTYPE_CHOICES.COOKIE,
            expires_at=self.now + timezone.timedelta(days=4),
        )
        context_obj = token.context_obj

        self.assertIsInstance(context_obj, ContextParams)

        self.assertEqual(context_obj.role, "editor")
        self.assertEqual(context_obj.permissions, ["read", "write"])
