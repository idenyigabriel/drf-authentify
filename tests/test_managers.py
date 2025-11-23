import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from drf_authentify.models import AuthToken
from drf_authentify.choices import AUTH_TYPES
from drf_authentify.utils.tokens import generate_access_token


User = get_user_model()


class AuthTokenManagerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username="user1", password="password")
        cls.user2 = User.objects.create_user(username="user2", password="password")

        # Generate unique access tokens for setup to avoid UNIQUE constraint failed error
        _, hash1 = generate_access_token()
        _, hash2 = generate_access_token()
        _, hash3 = generate_access_token()
        _, hash4 = generate_access_token()

        now = timezone.now()

        # 1. Expired Token (Expires yesterday)
        cls.expired_token = AuthToken.objects.create(
            user=cls.user1,
            auth_type=AUTH_TYPES.HEADER,
            access_token_hash=hash1,
            expires_at=now - datetime.timedelta(days=1),
            last_refreshed_at=now - datetime.timedelta(days=2),
        )

        # 2. Refreshable Token (Expires tomorrow, Refresh until next week)
        cls.refreshable_token = AuthToken.objects.create(
            user=cls.user1,
            auth_type=AUTH_TYPES.HEADER,
            access_token_hash=hash2,
            expires_at=now + datetime.timedelta(days=1),
            refresh_token_hash="refresh_hash_1",
            refresh_until=now + datetime.timedelta(days=7),
        )

        # 3. Active/Non-expiring Token (Expires None)
        cls.non_expiring_token = AuthToken.objects.create(
            user=cls.user2,
            auth_type=AUTH_TYPES.COOKIE,
            access_token_hash=hash3,
            expires_at=None,
        )

        # 4. Non-refreshable, Active Token (Expires tomorrow, No refresh token)
        cls.active_token = AuthToken.objects.create(
            user=cls.user2,
            auth_type=AUTH_TYPES.HEADER,
            access_token_hash=hash4,
            expires_at=now + datetime.timedelta(days=1),
        )

    ## QuerySet Method Tests

    def test_active_queryset(self):
        """Should return tokens that have not yet expired (future or None)."""
        qs = AuthToken.objects.active()
        self.assertEqual(qs.count(), 3)
        self.assertIn(self.refreshable_token, qs)
        self.assertIn(self.non_expiring_token, qs)
        self.assertIn(self.active_token, qs)
        self.assertNotIn(self.expired_token, qs)

    def test_refreshable_queryset(self):
        """Should return tokens with a refresh_token_hash and refresh_until in the future."""
        qs = AuthToken.objects.refreshable()
        self.assertEqual(qs.count(), 1)
        self.assertIn(self.refreshable_token, qs)
        self.assertNotIn(self.expired_token, qs)
        self.assertNotIn(self.active_token, qs)

    def test_expired_queryset(self):
        """Should return only the expired token."""
        qs = AuthToken.objects.expired()
        self.assertEqual(qs.count(), 1)
        self.assertIn(self.expired_token, qs)

    def test_for_user_queryset(self):
        """Should filter tokens by user."""
        qs1 = AuthToken.objects.for_user(self.user1)
        self.assertEqual(qs1.count(), 2)
        self.assertIn(self.expired_token, qs1)
        self.assertIn(self.refreshable_token, qs1)

        qs2 = AuthToken.objects.for_user(self.user2)
        self.assertEqual(qs2.count(), 2)

    def test_delete_expired(self):
        """Should delete expired tokens and return the correct count."""
        initial_count = AuthToken.objects.count()
        deleted_count = AuthToken.objects.delete_expired()

        self.assertEqual(deleted_count, 1)
        self.assertEqual(AuthToken.objects.count(), initial_count - 1)
        self.assertFalse(AuthToken.objects.filter(pk=self.expired_token.pk).exists())
        self.assertTrue(AuthToken.objects.filter(pk=self.refreshable_token.pk).exists())

    ## create_token Method Tests

    @patch("drf_authentify.managers.generate_access_token")
    @patch("drf_authentify.managers.generate_refresh_token")
    @patch("drf_authentify.managers.authentify_settings")
    def test_create_token_simple(
        self, mock_settings, mock_gen_refresh, mock_gen_access
    ):
        """Tests creation with default settings and no refresh token."""
        mock_settings.ENFORCE_SINGLE_LOGIN = False
        mock_settings.TOKEN_TTL = datetime.timedelta(minutes=30)
        mock_settings.REFRESH_TOKEN_TTL = None  # No refresh

        mock_gen_access.return_value = ("raw_access_3", "hashed_access_3")

        tokens = AuthToken.objects.create_token(self.user1, AUTH_TYPES.HEADER)

        self.assertEqual(tokens.access_token, "raw_access_3")
        self.assertIsNone(tokens.refresh_token)

        token_obj = tokens.token_instance
        self.assertEqual(token_obj.user, self.user1)
        self.assertEqual(token_obj.access_token_hash, "hashed_access_3")
        self.assertIsNotNone(token_obj.expires_at)
        self.assertAlmostEqual(
            token_obj.expires_at,
            timezone.now() + datetime.timedelta(minutes=30),
            delta=datetime.timedelta(seconds=2),
        )
        self.assertIsNone(token_obj.refresh_token_hash)
        self.assertIsNone(token_obj.refresh_until)
        mock_gen_refresh.assert_not_called()

    @patch("drf_authentify.managers.generate_access_token")
    @patch("drf_authentify.managers.generate_refresh_token")
    @patch("drf_authentify.managers.authentify_settings")
    def test_create_token_with_custom_ttl_and_refresh(
        self, mock_settings, mock_gen_refresh, mock_gen_access
    ):
        """Tests creation with custom timedelta and refresh token."""
        mock_settings.ENFORCE_SINGLE_LOGIN = False

        access_ttl = datetime.timedelta(hours=2)
        refresh_ttl = datetime.timedelta(days=30)

        mock_gen_access.return_value = ("raw_access_4", "hashed_access_4")
        mock_gen_refresh.return_value = ("raw_refresh_4", "hashed_refresh_4")

        tokens = AuthToken.objects.create_token(
            self.user2,
            AUTH_TYPES.COOKIE,
            access_expires_in=access_ttl,
            refresh_expires_in=refresh_ttl,
        )

        self.assertEqual(tokens.access_token, "raw_access_4")
        self.assertEqual(tokens.refresh_token, "raw_refresh_4")

        token_obj = tokens.token_instance  # Corrected to token_instance
        self.assertEqual(token_obj.access_token_hash, "hashed_access_4")
        self.assertEqual(token_obj.refresh_token_hash, "hashed_refresh_4")

        self.assertAlmostEqual(
            token_obj.expires_at,
            timezone.now() + access_ttl,
            delta=datetime.timedelta(seconds=2),
        )
        self.assertAlmostEqual(
            token_obj.refresh_until,
            timezone.now() + refresh_ttl,
            delta=datetime.timedelta(seconds=2),
        )
        mock_gen_refresh.assert_called_once()

    @patch("drf_authentify.managers.AuthTokenManager.filter")
    @patch("drf_authentify.managers.generate_access_token")
    @patch("drf_authentify.managers.authentify_settings")
    def test_create_token_enforce_single_login_delete(
        self, mock_settings, mock_gen_access, mock_filter
    ):
        """Tests single login enforcement with old tokens being deleted."""
        mock_settings.ENFORCE_SINGLE_LOGIN = True
        mock_settings.KEEP_EXPIRED_TOKENS = False
        mock_settings.TOKEN_TTL = datetime.timedelta(minutes=30)
        mock_settings.REFRESH_TOKEN_TTL = None

        mock_gen_access.return_value = ("raw_access_5", "hashed_access_5")

        # Mock queryset returned by self.filter(user=user)
        mock_qs = mock_filter.return_value
        mock_qs.delete.return_value = (5, {})

        AuthToken.objects.create_token(self.user1, AUTH_TYPES.HEADER)

        # Assert filter was called correctly
        mock_filter.assert_called_once_with(user=self.user1)
        # Assert delete was called
        mock_qs.delete.assert_called_once()
        # Assert update was NOT called
        mock_qs.update.assert_not_called()

    @patch("drf_authentify.managers.AuthTokenManager.filter")
    @patch("drf_authentify.managers.generate_access_token")
    @patch("drf_authentify.managers.authentify_settings")
    def test_create_token_enforce_single_login_soft_revoke(
        self, mock_settings, mock_gen_access, mock_filter
    ):
        """Tests single login enforcement with old tokens being soft-revoked/updated."""
        mock_settings.ENFORCE_SINGLE_LOGIN = True
        mock_settings.KEEP_EXPIRED_TOKENS = True
        mock_settings.TOKEN_TTL = datetime.timedelta(minutes=30)
        mock_settings.REFRESH_TOKEN_TTL = None

        mock_gen_access.return_value = ("raw_access_6", "hashed_access_6")

        # Mock queryset returned by self.filter(user=user)
        mock_qs = mock_filter.return_value

        AuthToken.objects.create_token(self.user2, AUTH_TYPES.HEADER)

        # Assert filter was called correctly
        mock_filter.assert_called_once_with(user=self.user2)
        # Assert delete was NOT called
        mock_qs.delete.assert_not_called()

        # Assert update was called with correct fields
        self.assertTrue(mock_qs.update.called)

        # Corrected: Access keyword arguments using call_args[1]
        update_kwargs = mock_qs.update.call_args[1]

        self.assertIn("revoked_at", update_kwargs)
        self.assertIn("expires_at", update_kwargs)
        self.assertIn("refresh_until", update_kwargs)

        self.assertLess(update_kwargs["expires_at"], timezone.now())
        self.assertLess(update_kwargs["refresh_until"], timezone.now())
