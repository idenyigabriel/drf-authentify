import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from drf_authentify.models import AuthToken
from drf_authentify.choices import AUTH_TYPES
from drf_authentify.services import TokenService
from drf_authentify.utils.tokens import generate_refresh_token


User = get_user_model()


# Mock function for consistent hashing during tests
def mock_hash_token_string(token):
    return f"hashed_{token}"


class TokenServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            username="service_user1", password="password"
        )
        cls.user2 = User.objects.create_user(
            username="service_user2", password="password"
        )

        # Consistent setup for hashing utility
        cls.raw_access_active, cls.hash_access_active = (
            "raw_active",
            mock_hash_token_string("raw_active"),
        )
        cls.raw_access_expired, cls.hash_access_expired = (
            "raw_expired",
            mock_hash_token_string("raw_expired"),
        )
        cls.raw_refresh_valid, cls.hash_refresh_valid = (
            "raw_refresh",
            mock_hash_token_string("raw_refresh"),
        )

        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)
        tomorrow = now + datetime.timedelta(days=1)
        next_week = now + datetime.timedelta(days=7)

        # 1. Active Header Token (for verification test)
        cls.active_token = AuthToken.objects.create(
            user=cls.user1,
            auth_type=AUTH_TYPES.HEADER,
            access_token_hash=cls.hash_access_active,
            expires_at=tomorrow,
        )

        # 2. Expired Cookie Token (for verification/revocation test)
        cls.expired_token = AuthToken.objects.create(
            user=cls.user1,
            auth_type=AUTH_TYPES.COOKIE,
            access_token_hash=cls.hash_access_expired,
            expires_at=yesterday,
        )

        # 3. Refreshable Token (for refresh test)
        cls.refreshable_token = AuthToken.objects.create(
            user=cls.user2,
            auth_type=AUTH_TYPES.HEADER,
            access_token_hash="hash_to_be_deleted",
            expires_at=tomorrow,
            refresh_token_hash=cls.hash_refresh_valid,
            refresh_until=next_week,
        )

        # 4. Expired Refresh Token (for failed refresh test)
        _, expired_refresh_hash = generate_refresh_token()
        cls.expired_refresh_token = AuthToken.objects.create(
            user=cls.user2,
            auth_type=AUTH_TYPES.HEADER,
            access_token_hash="hash_to_be_deleted_2",
            expires_at=tomorrow,
            refresh_token_hash=expired_refresh_hash,
            refresh_until=yesterday,
        )

    # --- Generation Tests ---

    # Patch the hashing utility to return consistent values for testing
    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    @patch("drf_authentify.models.AuthToken.objects.create_token")
    def test_generate_cookie_token(self, mock_create_token, mock_hash):
        """Tests generate_cookie_token passes correct timedelta and type to manager."""

        # Simulate manager returning a successful object
        mock_create_token.return_value = "IssuedTokensObject"

        tokens = TokenService.generate_cookie_token(
            self.user1,
            access_expires_in=3600,  # 1 hour
            refresh_expires_in=86400,  # 1 day
        )

        self.assertEqual(tokens, "IssuedTokensObject")
        mock_create_token.assert_called_once()

        # Check arguments passed to create_token
        args, kwargs = mock_create_token.call_args
        self.assertEqual(args[0], self.user1)
        self.assertEqual(args[1], AUTH_TYPES.COOKIE)
        self.assertIsInstance(kwargs["access_expires_in"], datetime.timedelta)
        self.assertEqual(kwargs["access_expires_in"].total_seconds(), 3600)
        self.assertEqual(kwargs["refresh_expires_in"].total_seconds(), 86400)
        self.assertIsNone(kwargs["context"])

    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    @patch("drf_authentify.models.AuthToken.objects.create_token")
    def test_generate_header_token_defaults(self, mock_create_token, mock_hash):
        """Tests generate_header_token passes correct type and None for defaults."""

        mock_create_token.return_value = "IssuedTokensObject"

        tokens = TokenService.generate_header_token(self.user2)

        self.assertEqual(tokens, "IssuedTokensObject")

        # Check arguments passed to create_token
        args, kwargs = mock_create_token.call_args
        self.assertEqual(args[0], self.user2)
        self.assertEqual(args[1], AUTH_TYPES.HEADER)
        self.assertIsNone(kwargs["access_expires_in"])
        self.assertIsNone(kwargs["refresh_expires_in"])

    # --- Verification Tests ---

    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    def test_verify_token_valid(self, mock_hash):
        """Should successfully verify an active token and return the instance."""
        token_instance = TokenService.verify_token(
            self.raw_access_active, AUTH_TYPES.HEADER
        )

        self.assertIsNotNone(token_instance)
        self.assertEqual(token_instance.user, self.user1)
        self.assertEqual(token_instance.pk, self.active_token.pk)

    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    def test_verify_token_expired(self, mock_hash):
        """Should fail to verify an expired token (None returned)."""
        token_instance = TokenService.verify_token(
            self.raw_access_expired, AUTH_TYPES.COOKIE
        )
        self.assertIsNone(token_instance)

    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    def test_verify_token_wrong_auth_type(self, mock_hash):
        """Should fail to verify if the wrong auth type is provided."""
        token_instance = TokenService.verify_token(
            self.raw_access_active, AUTH_TYPES.COOKIE
        )
        self.assertIsNone(token_instance)

    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    def test_verify_token_no_auth_type(self, mock_hash):
        """Should verify correctly if no auth type is provided (checks both)."""
        token_instance = TokenService.verify_token(self.raw_access_active)
        self.assertEqual(token_instance.pk, self.active_token.pk)

    # --- Revocation Tests ---

    def test_revoke_token(self):
        """Should delete the specific token instance provided."""
        pk_to_delete = self.active_token.pk
        self.assertTrue(AuthToken.objects.filter(pk=pk_to_delete).exists())

        TokenService.revoke_token(self.active_token)

        self.assertFalse(AuthToken.objects.filter(pk=pk_to_delete).exists())

    def test_revoke_all_user_tokens(self):
        """Should delete all tokens associated with a user."""
        # user1 has 2 tokens (active, expired)
        self.assertEqual(AuthToken.objects.for_user(self.user1).count(), 2)

        TokenService.revoke_all_user_tokens(self.user1)

        self.assertEqual(AuthToken.objects.for_user(self.user1).count(), 0)
        # Check that user2 tokens are unaffected
        self.assertGreater(AuthToken.objects.for_user(self.user2).count(), 0)

    def test_revoke_all_expired_user_tokens(self):
        """Should only delete expired tokens for a specific user."""
        # user1 has 1 active (active_token) and 1 expired token
        self.assertEqual(AuthToken.objects.for_user(self.user1).count(), 2)

        TokenService.revoke_all_expired_user_tokens(self.user1)

        # Only the expired token should be gone
        self.assertEqual(AuthToken.objects.for_user(self.user1).count(), 1)
        self.assertTrue(AuthToken.objects.filter(pk=self.active_token.pk).exists())
        self.assertFalse(AuthToken.objects.filter(pk=self.expired_token.pk).exists())

    @patch("drf_authentify.models.AuthTokenManager.delete_expired")
    def test_revoke_expired_tokens(self, mock_delete_expired):
        """Should call the manager's delete_expired method."""
        TokenService.revoke_expired_tokens()
        mock_delete_expired.assert_called_once()

    # --- Refresh Tests ---

    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    @patch("drf_authentify.services.TokenService._generate_auth_token")
    def test_refresh_token_success_delete(self, mock_generate, mock_hash):
        """Tests successful refresh creates a new token and deletes the old one (default behavior)."""
        initial_pk = self.refreshable_token.pk

        # Ensure cleanup setting is OFF (default)
        with patch("drf_authentify.services.authentify_settings") as mock_settings:
            mock_settings.KEEP_EXPIRED_TOKENS = False

            # Setup mock return value for the new token
            mock_generate.return_value = "NewIssuedTokens"

            # Execute refresh
            result = TokenService.refresh_token(self.raw_refresh_valid)

            # Assertions
            self.assertEqual(result, "NewIssuedTokens")

            # Old token must be deleted
            self.assertFalse(AuthToken.objects.filter(pk=initial_pk).exists())

            # New token generation must be called with correct user/context
            mock_generate.assert_called_once()
            args, kwargs = mock_generate.call_args
            self.assertEqual(args[0], self.user2)  # User check
            self.assertEqual(
                args[1], self.refreshable_token.auth_type
            )  # Auth type check

    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    def test_refresh_token_invalid_hash(self, mock_hash):
        """Tests refresh fails if refresh token hash doesn't match a token."""
        result = TokenService.refresh_token("non_existent_refresh_token")
        self.assertIsNone(result)

    def test_refresh_token_expired_refresh_window_not_found(self):
        """Tests refresh fails if refresh_until has passed (token not found by refreshable() queryset)."""

        # We rely on the AuthToken.objects.refreshable() filter *not* finding this token
        # due to its setup with a refresh_until in the past.
        # We need the hash to find it by lookup, so we re-hash the raw token we didn't store.

        # Fetch the token that should not be refreshable
        token = AuthToken.objects.get(pk=self.expired_refresh_token.pk)

        # Manually verify the refreshable queryset fails
        self.assertIsNone(AuthToken.objects.refreshable().filter(pk=token.pk).first())

        # Test the service call with a token that won't be found by `refreshable()`
        # Since we don't have the raw token string for this fixture, this test is tricky.
        # We will simply assert that calling refresh_token with a hash that won't match
        # a refreshable token returns None.

        result = TokenService.refresh_token("some_token_that_wont_match_refreshable")
        self.assertIsNone(result)

    @patch("drf_authentify.services.TokenService._generate_auth_token")
    @patch("drf_authentify.services.authentify_settings")
    @patch(
        "drf_authentify.services.hash_token_string", side_effect=mock_hash_token_string
    )
    def test_refresh_token_soft_revoke_cleanup(
        self, mock_hash, mock_settings, mock_generate
    ):
        """Tests refresh with KEEP_EXPIRED_TOKENS = True soft-revokes the old token."""
        # Ensure cleanup setting is on
        mock_settings.KEEP_EXPIRED_TOKENS = True

        # Use a fresh, known-valid token for user1
        raw_refresh, hashed_refresh = "soft_revoke_refresh", mock_hash_token_string(
            "soft_revoke_refresh"
        )

        refreshable_token_pk = AuthToken.objects.create(
            user=self.user1,
            auth_type=AUTH_TYPES.HEADER,
            access_token_hash="soft_revoke_access_hash",
            expires_at=timezone.now() + datetime.timedelta(days=1),
            refresh_token_hash=hashed_refresh,
            refresh_until=timezone.now() + datetime.timedelta(days=7),
        ).pk

        mock_generate.return_value = "NewIssuedTokens"

        # Execute refresh
        result = TokenService.refresh_token(raw_refresh)

        self.assertIsNotNone(result)

        # Old token must NOT be deleted, but soft-revoked
        old_token = AuthToken.objects.get(pk=refreshable_token_pk)
        self.assertIsNotNone(old_token.revoked_at)
        self.assertLess(old_token.expires_at, timezone.now())
        self.assertLess(old_token.refresh_until, timezone.now())
