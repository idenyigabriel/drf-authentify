from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import HttpRequest
from time import sleep
from datetime import timedelta

from drf_authentify.models import AuthToken
from drf_authentify.services import TokenService
from drf_authentify.choices import AUTHTYPE_CHOICES


User = get_user_model()


class TestTokenService(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="testpass")

    def test_generate_header_token_creates_valid_token(self):
        token_str = TokenService.generate_header_token(self.user)
        token_obj = AuthToken.objects.get(token=token_str)

        self.assertEqual(token_obj.user, self.user)
        self.assertEqual(token_obj.auth_type, AUTHTYPE_CHOICES.HEADER)
        self.assertGreater(token_obj.expires_at, timezone.now())

    def test_generate_cookie_token_creates_valid_token(self):
        token_str = TokenService.generate_cookie_token(
            self.user, context={"ip": "127.0.0.1"}
        )
        token_obj = AuthToken.objects.get(token=token_str)

        self.assertEqual(token_obj.auth_type, AUTHTYPE_CHOICES.COOKIE)
        self.assertIn("ip", token_obj.context)

    def test_token_expiration(self):
        token_str = TokenService.generate_header_token(self.user, expires_in=1)
        token_obj = AuthToken.objects.get(token=token_str)
        self.assertTrue(token_obj.expires_at <= timezone.now() + timedelta(seconds=2))

        sleep(2)
        TokenService.revoke_expired_tokens()
        self.assertFalse(AuthToken.objects.filter(token=token_str).exists())

    def test_verify_token_success_and_failure(self):
        token_str = TokenService.generate_header_token(self.user)
        token = TokenService.verify_token(token_str, auth_type=AUTHTYPE_CHOICES.HEADER)
        self.assertIsNotNone(token)
        self.assertEqual(token.token, token_str)

        invalid = TokenService.verify_token("invalid_token")
        self.assertIsNone(invalid)

    def test_revoke_token_from_request(self):
        token_str = TokenService.generate_cookie_token(self.user)
        token = AuthToken.objects.get(token=token_str)

        request = HttpRequest()
        request.auth = token

        TokenService.revoke_token_from_request(request)
        self.assertFalse(AuthToken.objects.filter(token=token_str).exists())

    def test_revoke_all_tokens_for_user_from_request(self):
        TokenService.generate_header_token(self.user)
        TokenService.generate_cookie_token(self.user)

        self.assertEqual(AuthToken.objects.filter(user=self.user).count(), 2)

        request = HttpRequest()
        request.user = self.user

        TokenService.revoke_all_tokens_for_user_from_request(request)
        self.assertEqual(AuthToken.objects.filter(user=self.user).count(), 0)

    def test_revoke_all_user_tokens(self):
        TokenService.generate_cookie_token(self.user)
        TokenService.generate_header_token(self.user)

        TokenService.revoke_all_user_tokens(self.user)
        self.assertFalse(AuthToken.objects.filter(user=self.user).exists())

    def test_token_uniqueness(self):
        """Ensure generated tokens are unique across attempts."""
        tokens = set()
        for _ in range(10):
            token = TokenService.generate_header_token(self.user)
            self.assertNotIn(token, tokens)
            tokens.add(token)

    @override_settings(AUTHENTIFY_MAX_TOKEN_CREATION_ATTEMPTS=1)
    def test_generate_token_raises_on_excessive_collisions(self):
        # Patch generate_token to always return a duplicate
        from drf_authentify import utils

        existing = TokenService.generate_header_token(self.user)
        original_generate_token = utils.generate_token
        utils.generate_token = lambda: existing  # always return same token

        with self.assertRaises(RuntimeError):
            TokenService.generate_header_token(self.user)

        # Restore original
        utils.generate_token = original_generate_token
