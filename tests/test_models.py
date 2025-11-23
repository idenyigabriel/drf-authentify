import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model

from drf_authentify.choices import AUTH_TYPES
from drf_authentify.contexts import ContextParams
from drf_authentify.models import AuthToken, get_token_model, AbstractAuthToken


User = get_user_model()


class AuthTokenModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="password")
        cls.token = AuthToken.objects.create(
            user=cls.user,
            access_token_hash="test_access_hash",
            refresh_token_hash="test_refresh_hash",
            auth_type=AUTH_TYPES.HEADER,
            context={"ip": "127.0.0.1"},
            expires_at=timezone.now() + datetime.timedelta(hours=1),
        )

    ## Model Field and Constraint Tests

    def test_model_fields_exist(self):
        """Ensures all required fields are present and correctly typed."""
        fields = [f.name for f in AuthToken._meta.get_fields()]
        expected_fields = [
            "access_token_hash",
            "refresh_token_hash",
            "auth_type",
            "context",
            "last_refreshed_at",
            "refresh_until",
            "expires_at",
            "created_at",
            "revoked_at",
            "user",
            "id",
        ]
        for field in expected_fields:
            self.assertIn(field, fields)

    def test_token_hash_uniqueness(self):
        with self.assertRaises(IntegrityError):
            AuthToken.objects.create(
                user=self.user,
                access_token_hash="test_access_hash",  # Duplicate hash
                auth_type=AUTH_TYPES.COOKIE,
            )

    def test_default_context(self):
        token = AuthToken.objects.create(
            user=self.user,
            access_token_hash="unique_hash_1",
            auth_type=AUTH_TYPES.HEADER,
        )
        self.assertEqual(token.context, {})

    ## Property Tests

    def test_is_expired_false(self):
        self.assertFalse(self.token.is_expired)

    def test_is_expired_true(self):
        self.token.expires_at = timezone.now() - datetime.timedelta(minutes=1)
        self.token.save()
        self.assertTrue(self.token.is_expired)

    def test_is_expired_null(self):
        self.token.expires_at = None
        self.token.save()
        self.assertFalse(self.token.is_expired)

    def test_context_obj_property(self):
        context_obj = self.token.context_obj
        self.assertIsInstance(context_obj, ContextParams)
        self.assertEqual(context_obj.ip, "127.0.0.1")

    def test_str_representation(self):
        self.assertEqual(str(self.token), f"{self.user} ({AUTH_TYPES.HEADER})")


class GetTokenModelTests(TestCase):
    @patch("drf_authentify.models.authentify_settings")
    def test_default_model_path(self, mock_settings):
        mock_settings.TOKEN_MODEL = "drf_authentify.AuthToken"
        model = get_token_model()
        self.assertIs(model, AuthToken)

    @patch("drf_authentify.models.authentify_settings")
    def test_custom_model_path_via_app(self, mock_settings):
        # Define the necessary Meta class
        class CustomTokenMeta:
            app_label = "custom_app"
            abstract = False  # Must not be abstract to be retrieved by apps.get_model

        # Add __module__ and Meta class to attributes
        mock_model = type(
            "CustomToken",
            (AbstractAuthToken,),
            {"__module__": __name__, "Meta": CustomTokenMeta},
        )

        with patch(
            "drf_authentify.models.apps.get_model", return_value=mock_model
        ) as mock_get_model:
            mock_settings.TOKEN_MODEL = "custom_app.CustomToken"
            model = get_token_model()

            self.assertIs(model, mock_model)
            mock_get_model.assert_called_once_with("custom_app", "CustomToken")

    @patch("drf_authentify.models.authentify_settings")
    def test_direct_import_path(self, mock_settings):
        # Define the necessary Meta class
        class DirectImportTokenMeta:
            app_label = "drf_authentify"  # Can use the main app_label
            abstract = False

        # Add __module__ and Meta class to attributes
        mock_model = type(
            "DirectImportToken",
            (AbstractAuthToken,),
            {"__module__": __name__, "Meta": DirectImportTokenMeta},
        )

        with patch(
            "drf_authentify.models.import_string", return_value=mock_model
        ) as mock_import_string:
            mock_settings.TOKEN_MODEL = "path_to_token_model"
            model = get_token_model()

            self.assertIs(model, mock_model)
            mock_import_string.assert_called_once_with("path_to_token_model")
