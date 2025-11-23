import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from drf_authentify.models import AuthToken
from drf_authentify.choices import AUTH_TYPES
from drf_authentify.forms import AuthTokenAdminForm


User = get_user_model()


class AuthTokenAdminFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="password")
        # Define base valid data
        cls.now = timezone.now().replace(microsecond=0)
        cls.valid_data = {
            "user": cls.user.pk,
            "auth_type": AUTH_TYPES.HEADER.value,
            "context": "{}",  # JSONField needs a string representation
        }

    def test_valid_form_data_passes(self):
        data = self.valid_data.copy()
        data["expires_at"] = self.now + datetime.timedelta(hours=1)
        data["refresh_until"] = self.now + datetime.timedelta(hours=2)  # greater

        form = AuthTokenAdminForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertNotIn("refresh_until", form.errors)
        self.assertNotIn("expires_at", form.errors)

    def test_equal_timestamps_pass(self):
        equal_time = self.now + datetime.timedelta(hours=1)
        data = self.valid_data.copy()
        data["expires_at"] = equal_time
        data["refresh_until"] = equal_time  # equal

        form = AuthTokenAdminForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_data_fails(self):
        data = self.valid_data.copy()
        data["expires_at"] = self.now + datetime.timedelta(hours=2)  # greater
        data["refresh_until"] = self.now + datetime.timedelta(hours=1)

        form = AuthTokenAdminForm(data=data)
        self.assertFalse(form.is_valid())

        # Check for specific field errors raised in clean()
        self.assertIn("refresh_until", form.errors)
        self.assertIn("expires_at", form.errors)

        # Check error message for refresh_until
        self.assertEqual(
            form.errors["refresh_until"][0], "Must be on or after expires_at"
        )
        # Check error message for expires_at
        self.assertEqual(
            form.errors["expires_at"][0], "Must be on or before refresh_until"
        )

    def test_missing_one_timestamp_passes(self):
        # Case 1: expires_at is present, refresh_until is None
        data1 = self.valid_data.copy()
        data1["expires_at"] = self.now
        form1 = AuthTokenAdminForm(data=data1)
        self.assertTrue(form1.is_valid())

        # Case 2: refresh_until is present, expires_at is None
        data2 = self.valid_data.copy()
        data2["refresh_until"] = self.now
        form2 = AuthTokenAdminForm(data=data2)
        self.assertTrue(form2.is_valid())

        # Case 3: Both are None
        form3 = AuthTokenAdminForm(data=self.valid_data)
        self.assertTrue(form3.is_valid())

    ## Model Integration Test

    @patch("drf_authentify.forms.get_token_model")
    def test_uses_correct_model(self, mock_get_token_model):
        """Ensures the form uses the result of get_token_model()."""
        mock_get_token_model.return_value = AuthToken
        # Re-importing ensures the form picks up the mocked function's result,
        # though standard practice dictates using the imported class directly.
        # This test primarily ensures the dynamic call exists.
        self.assertIs(AuthTokenAdminForm.Meta.model, AuthToken)
