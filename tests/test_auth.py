from datetime import timedelta
from unittest.mock import patch, Mock
from rest_framework.exceptions import AuthenticationFailed

from django.utils import timezone
from django.test import TestCase, RequestFactory


from drf_authentify.settings import authentify_settings
from drf_authentify.auth import CookieAuthentication, AuthorizationHeaderAuthentication


class MockUser:
    def __init__(self, active=True, name="U"):
        self.is_active = active
        self.name = name

    def __repr__(self):
        return self.name


class MockToken:
    def __init__(self, user, created_at, last_refreshed_at, expires_at):
        self.user = user
        self.created_at = created_at
        self.last_refreshed_at = last_refreshed_at
        self.expires_at = expires_at
        self.refresh_until = expires_at

    def save(self, update_fields=None):
        pass

    def __repr__(self):
        return f"T({self.user})"


class AuthTests(TestCase):

    def setUp(self):
        self.rf = RequestFactory()

    #
    # BASIC HEADER PARSING TESTS
    #

    def test_header_missing_returns_none(self):
        req = self.rf.get("/")
        auth = AuthorizationHeaderAuthentication()
        self.assertIsNone(auth._get_token_from_request(req))

    def test_header_invalid_format(self):
        req = self.rf.get("/", HTTP_AUTHORIZATION="InvalidFormat")
        auth = AuthorizationHeaderAuthentication()
        with self.assertRaises(AuthenticationFailed):
            auth._get_token_from_request(req)

    def test_header_invalid_prefix(self):
        req = self.rf.get("/", HTTP_AUTHORIZATION="BAD token123")
        auth = AuthorizationHeaderAuthentication()
        with self.assertRaises(AuthenticationFailed):
            auth._get_token_from_request(req)

    def test_header_valid(self):
        prefix = authentify_settings.AUTH_HEADER_PREFIXES[0]
        req = self.rf.get("/", HTTP_AUTHORIZATION=f"{prefix} abc123")
        auth = AuthorizationHeaderAuthentication()
        self.assertEqual(auth._get_token_from_request(req), "abc123")

    #
    # COOKIE PARSING
    #

    def test_cookie_parsing(self):
        req = self.rf.get("/")
        req.COOKIES["auth"] = "cookie_token"
        auth = CookieAuthentication()
        with patch.object(authentify_settings, "AUTH_COOKIE_NAMES", ["auth"]):
            tok = auth._get_token_from_request(req)

        self.assertEqual(tok, "cookie_token")

    #
    # AUTHENTICATION + AUTO REFRESH
    #

    @patch("drf_authentify.auth.load_handler", return_value=None)
    @patch("drf_authentify.services.TokenService.verify_token")
    def test_authenticate_happy_path(self, verify, load_handler):
        user = MockUser(True)
        tok = MockToken(
            user, timezone.now(), timezone.now(), timezone.now() + timedelta(minutes=5)
        )

        verify.return_value = tok

        req = self.rf.get(
            "/", HTTP_AUTHORIZATION=f"{authentify_settings.AUTH_HEADER_PREFIXES[0]} abc"
        )

        auth = AuthorizationHeaderAuthentication()
        u, t = auth.authenticate(req)

        self.assertEqual(u, user)
        self.assertEqual(t, tok)

    #
    # AUTO REFRESH UPDATES TOKEN
    #

    @patch("drf_authentify.auth.load_handler", return_value=None)
    @patch("drf_authentify.services.TokenService.verify_token")
    def test_auto_refresh_updates_token(self, verify, load_handler):

        now = timezone.now()
        user = MockUser(True)
        tok = MockToken(
            user=user,
            created_at=now - timedelta(hours=1),
            last_refreshed_at=now - timedelta(hours=1),
            expires_at=now + timedelta(minutes=30),
        )
        verify.return_value = tok

        old = tok.last_refreshed_at

        with (
            patch.object(authentify_settings, "AUTO_REFRESH", True),
            patch.object(
                authentify_settings, "AUTO_REFRESH_INTERVAL", timedelta(seconds=1)
            ),
            patch.object(authentify_settings, "TOKEN_TTL", timedelta(minutes=5)),
            patch.object(
                authentify_settings, "AUTO_REFRESH_MAX_TTL", timedelta(hours=2)
            ),
            patch.object(authentify_settings, "REFRESH_TOKEN_TTL", timedelta(hours=1)),
            patch("django.utils.timezone.now", return_value=old + timedelta(seconds=2)),
        ):

            req = self.rf.get(
                "/",
                HTTP_AUTHORIZATION=f"{authentify_settings.AUTH_HEADER_PREFIXES[0]} token",
            )
            auth = AuthorizationHeaderAuthentication()
            auth.authenticate(req)

        # Should be updated
        self.assertGreater(tok.last_refreshed_at, old)

    #
    # AUTO REFRESH HANDLER
    #

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_auto_refresh_handler_runs(self, verify):
        handler = Mock()

        now = timezone.now()
        U1 = MockUser(True, "U1")
        T1 = MockToken(
            user=U1,
            created_at=now - timedelta(hours=1),
            last_refreshed_at=now - timedelta(hours=1),
            expires_at=now + timedelta(minutes=30),
        )
        verify.return_value = T1

        handler.return_value = (U1, T1)

        # Fake load_handler: only return `handler` for POST_AUTO_REFRESH_HANDLER
        def fake_load(name, setting_name, args):
            if setting_name == "POST_AUTO_REFRESH_HANDLER":
                return handler
            return None

        with (
            patch.object(authentify_settings, "AUTO_REFRESH", True),
            patch.object(
                authentify_settings, "AUTO_REFRESH_INTERVAL", timedelta(seconds=1)
            ),
            patch.object(authentify_settings, "TOKEN_TTL", timedelta(minutes=5)),
            patch.object(
                authentify_settings, "AUTO_REFRESH_MAX_TTL", timedelta(hours=2)
            ),
            patch.object(authentify_settings, "REFRESH_TOKEN_TTL", timedelta(hours=1)),
            patch("drf_authentify.auth.load_handler", side_effect=fake_load),
            patch(
                "django.utils.timezone.now",
                return_value=T1.last_refreshed_at + timedelta(seconds=2),
            ),
        ):

            req = self.rf.get(
                "/",
                HTTP_AUTHORIZATION=f"{authentify_settings.AUTH_HEADER_PREFIXES[0]} t",
            )
            auth = AuthorizationHeaderAuthentication()
            auth.authenticate(req)

        handler.assert_called_once_with(U1, T1, "t")
