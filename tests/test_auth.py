from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory

from drf_authentify.choices import AUTHTYPE_CHOICES
from drf_authentify.settings import authentify_settings
from drf_authentify.auth.authentication import (
    BaseTokenAuth,
    CookieAuthentication,
    AuthorizationHeaderAuthentication,
)


class BaseTokenAuthTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mock_token = MagicMock()
        self.mock_token.user = MagicMock()

    def test_base_token_auth_abstract_get_token(self):
        class ConcreteBaseTokenAuth(BaseTokenAuth):
            source = "test"
            auth_type = "TEST"

            def _get_token_from_request(self, request):
                raise NotImplementedError("Must implement _get_token_from_request")

        auth = ConcreteBaseTokenAuth()
        request = self.factory.get("/")
        with self.assertRaises(NotImplementedError):
            auth._get_token_from_request(request)

    def test_base_token_auth_authenticate_header_method(self):
        class ConcreteBaseTokenAuth(BaseTokenAuth):
            source = "Test Source"
            auth_type = "TEST"

            def _get_token_from_request(self, request):
                return "test_token"

        auth = ConcreteBaseTokenAuth()
        request = self.factory.get("/")
        header = auth.authenticate_header(request)
        self.assertEqual(header, 'Test Source="api"')

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_base_token_auth_authenticate_success_with_auth_type(
        self, mock_verify_token
    ):
        class ConcreteBaseTokenAuth(BaseTokenAuth):
            source = "test"
            auth_type = AUTHTYPE_CHOICES.HEADER

            def _get_token_from_request(self, request):
                return "valid_token"

        mock_verify_token.return_value = self.mock_token
        auth = ConcreteBaseTokenAuth()
        request = self.factory.get("/")
        user, token = auth.authenticate(request)
        mock_verify_token.assert_called_once_with("valid_token")
        self.assertEqual(user, self.mock_token.user)
        self.assertEqual(token, self.mock_token)

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_base_token_auth_authenticate_success_without_auth_type(
        self, mock_verify_token
    ):
        class ConcreteBaseTokenAuth(BaseTokenAuth):
            source = "test"
            auth_type = None

            def _get_token_from_request(self, request):
                return "valid_token"

        mock_verify_token.return_value = self.mock_token
        auth = ConcreteBaseTokenAuth()
        request = self.factory.get("/")
        user, token = auth.authenticate(request)
        mock_verify_token.assert_called_once_with("valid_token")
        self.assertEqual(user, self.mock_token.user)
        self.assertEqual(token, self.mock_token)

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_base_token_auth_authenticate_failure_invalid_token(
        self, mock_verify_token
    ):
        class ConcreteBaseTokenAuth(BaseTokenAuth):
            source = "test"
            auth_type = AUTHTYPE_CHOICES.COOKIE

            def _get_token_from_request(self, request):
                return "invalid_token"

        mock_verify_token.return_value = None
        auth = ConcreteBaseTokenAuth()
        request = self.factory.get("/")
        result = auth.authenticate(request)
        self.assertIsNone(result)

    def test_base_token_auth_authenticate_failure_no_token(self):
        class ConcreteBaseTokenAuth(BaseTokenAuth):
            source = "test"
            auth_type = AUTHTYPE_CHOICES.HEADER

            def _get_token_from_request(self, request):
                return None

        auth = ConcreteBaseTokenAuth()
        request = self.factory.get("/")
        result = auth.authenticate(request)
        self.assertIsNone(result)


class AuthorizationHeaderAuthenticationTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mock_token = MagicMock()
        self.mock_token.user = MagicMock()

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_auth_header_auth_success(self, mock_verify_token):
        mock_verify_token.return_value = self.mock_token
        auth = AuthorizationHeaderAuthentication()

        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = (
            f"{authentify_settings.ALLOWED_HEADER_PREFIXES[0]} validtoken123"
        )

        user, token = auth.authenticate(request)

        mock_verify_token.assert_called_once_with("validtoken123")
        self.assertEqual(user, self.mock_token.user)
        self.assertEqual(token, self.mock_token)

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_auth_header_auth_failure(self, mock_verify_token):
        mock_verify_token.return_value = None
        auth = AuthorizationHeaderAuthentication()

        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = (
            f"{authentify_settings.ALLOWED_HEADER_PREFIXES[0]} invalidtoken"
        )
        result = auth.authenticate(request)

        self.assertIsNone(result)

    def test_auth_header_invalid_format_no_space(self):
        auth = AuthorizationHeaderAuthentication()
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = (
            f"{authentify_settings.ALLOWED_HEADER_PREFIXES[0]}invalidtoken"
        )
        result = auth.authenticate(request)
        self.assertIsNone(result)

    def test_auth_header_invalid_format_too_many_parts(self):
        auth = AuthorizationHeaderAuthentication()
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = (
            f"{authentify_settings.ALLOWED_HEADER_PREFIXES[0]} extra part token"
        )
        result = auth.authenticate(request)
        self.assertIsNone(result)

    def test_auth_header_invalid_prefix(self):
        auth = AuthorizationHeaderAuthentication()
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = "WrongPrefix invalidtoken"
        result = auth.authenticate(request)
        self.assertIsNone(result)

    def test_auth_header_no_authorization_header(self):
        auth = AuthorizationHeaderAuthentication()
        request = self.factory.get("/")
        result = auth.authenticate(request)
        self.assertIsNone(result)


class CookieAuthenticationTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mock_token = MagicMock()
        self.mock_token.user = MagicMock()

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_cookie_auth_success(self, mock_verify_token):
        mock_verify_token.return_value = self.mock_token
        auth = CookieAuthentication()

        request = self.factory.get("/")
        request.COOKIES[authentify_settings.COOKIE_KEY] = "validcookie123"

        user, token = auth.authenticate(request)

        mock_verify_token.assert_called_once_with("validcookie123")
        self.assertEqual(user, self.mock_token.user)
        self.assertEqual(token, self.mock_token)

    @patch("drf_authentify.services.TokenService.verify_token")
    def test_cookie_auth_failure(self, mock_verify_token):
        mock_verify_token.return_value = None
        auth = CookieAuthentication()

        request = self.factory.get("/")
        request.COOKIES[authentify_settings.COOKIE_KEY] = "invalidcookie"
        result = auth.authenticate(request)

        self.assertIsNone(result)

    def test_cookie_auth_no_cookie(self):
        auth = CookieAuthentication()
        request = self.factory.get("/")
        result = auth.authenticate(request)
        self.assertIsNone(result)
