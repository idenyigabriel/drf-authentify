import datetime
from unittest.mock import patch

from django.utils import timezone
from django.contrib.admin import site
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from drf_authentify.models import AuthToken
from drf_authentify.choices import AUTH_TYPES
from drf_authentify.admin import AuthTokenAdmin, ExpirationStatusFilter
from drf_authentify.utils.tokens import generate_access_token, generate_refresh_token


User = get_user_model()


class AuthTokenAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="adminuser", password="password")
        cls.factory = RequestFactory()

        now = timezone.now()

        # 1. Expired Token
        AuthToken.objects.create(
            user=cls.user,
            access_token_hash=generate_access_token()[1],
            auth_type=AUTH_TYPES.HEADER,
            context={},
            expires_at=now - datetime.timedelta(days=1),
            refresh_token_hash=generate_refresh_token()[1],
            refresh_until=now + datetime.timedelta(days=7),
        )

        # 2. Valid Token (Expires in future)
        AuthToken.objects.create(
            user=cls.user,
            access_token_hash=generate_access_token()[1],
            auth_type=AUTH_TYPES.HEADER,
            context={},
            expires_at=now + datetime.timedelta(days=1),
        )

        # 3. Valid Token (Never expires)
        AuthToken.objects.create(
            user=cls.user,
            access_token_hash=generate_access_token()[1],
            auth_type=AUTH_TYPES.COOKIE,
            context={},
            expires_at=None,
        )

    ## Filter Tests

    def test_expiration_status_filter_expired(self):
        request = self.factory.get("/")
        # Pass None for model_admin to avoid pickling issues
        filter_instance = ExpirationStatusFilter(
            request, {"expiration": "expired"}, AuthToken, None
        )

        queryset = filter_instance.queryset(request, AuthToken.objects.all())
        self.assertEqual(queryset.count(), 1)
        self.assertTrue(queryset.first().is_expired)

    def test_expiration_status_filter_valid(self):
        request = self.factory.get("/")
        filter_instance = ExpirationStatusFilter(
            request, {"expiration": "valid"}, AuthToken, None
        )

        queryset = filter_instance.queryset(request, AuthToken.objects.all())
        self.assertEqual(queryset.count(), 2)
        for token in queryset:
            self.assertFalse(token.is_expired)

    ## Custom Admin Method Tests

    def test_is_valid_method(self):
        admin_instance = AuthTokenAdmin(AuthToken, site)

        valid_token = AuthToken.objects.filter(expires_at__isnull=True).first()
        expired_token = AuthToken.objects.filter(
            expires_at__isnull=False, expires_at__lt=timezone.now()
        ).first()

        self.assertTrue(admin_instance.is_valid(valid_token))
        self.assertFalse(admin_instance.is_valid(expired_token))
        self.assertTrue(admin_instance.is_valid.boolean)

    ## save_model Tests (Creation)

    @patch("drf_authentify.admin.generate_access_token")
    @patch("drf_authentify.admin.generate_refresh_token")
    def test_save_model_on_creation_with_refresh(
        self, mock_gen_refresh, mock_gen_access
    ):
        """
        Tests that on creating a new token with a refresh_until date,
        both tokens are generated and messages are sent.
        """
        admin_instance = AuthTokenAdmin(AuthToken, site)

        raw_access, hashed_access = "raw_access_1", "hashed_access_1"
        raw_refresh, hashed_refresh = "raw_refresh_1", "hashed_refresh_1"
        mock_gen_access.return_value = (raw_access, hashed_access)
        mock_gen_refresh.return_value = (raw_refresh, hashed_refresh)

        # 1. Prepare Request and Form
        request = self.factory.post("/")
        request.user = self.user
        request._messages = []

        new_token_data = model_to_dict(AuthToken())
        new_token_data.update(
            {
                "user": self.user.pk,
                "auth_type": AUTH_TYPES.COOKIE.value,
                "context": "{}",  # Ensure JSONField data is present
                "expires_at": timezone.now() + datetime.timedelta(days=5),
                "refresh_until": timezone.now() + datetime.timedelta(days=10),
            }
        )
        form = admin_instance.form(data=new_token_data)
        self.assertTrue(form.is_valid(), form.errors)

        # FIX: Call form.save(commit=False) to populate the instance with form data
        token_obj = form.save(commit=False)

        # 2. Call save_model
        with patch.object(admin_instance, "message_user") as mock_message_user:
            admin_instance.save_model(request, token_obj, form, change=False)

            # 3. Assertions

            self.assertEqual(token_obj.access_token_hash, hashed_access)
            self.assertEqual(token_obj.refresh_token_hash, hashed_refresh)

            mock_message_user.assert_any_call(request, f"🗝 Access Token:\n{raw_access}")
            mock_message_user.assert_any_call(
                request, f"🔄 Refresh Token:\n{raw_refresh}"
            )
            self.assertEqual(mock_message_user.call_count, 2)

    @patch("drf_authentify.admin.generate_access_token")
    def test_save_model_on_creation_no_refresh(self, mock_gen_access):
        """
        Tests that on creating a new token without refresh_until, only the access token is generated.
        """
        admin_instance = AuthTokenAdmin(AuthToken, site)

        raw_access, hashed_access = "raw_access_2", "hashed_access_2"
        mock_gen_access.return_value = (raw_access, hashed_access)

        request = self.factory.post("/")
        request.user = self.user
        request._messages = []

        new_token_data = model_to_dict(AuthToken())
        new_token_data.update(
            {
                "user": self.user.pk,
                "auth_type": AUTH_TYPES.COOKIE.value,
                "context": "{}",  # Ensure JSONField data is present
                "expires_at": timezone.now() + datetime.timedelta(days=5),
                "refresh_until": None,
            }
        )
        form = admin_instance.form(data=new_token_data)
        self.assertTrue(form.is_valid(), form.errors)

        # FIX: Call form.save(commit=False) to populate the instance with form data
        token_obj = form.save(commit=False)

        with patch.object(admin_instance, "message_user") as mock_message_user:
            admin_instance.save_model(request, token_obj, form, change=False)

            self.assertEqual(token_obj.access_token_hash, hashed_access)
            self.assertIsNone(token_obj.refresh_token_hash)

            mock_message_user.assert_called_once_with(
                request, f"🗝 Access Token:\n{raw_access}"
            )

    def test_save_model_on_change(self):
        """
        Tests that when editing an existing token (change=True), no tokens are regenerated
        and no messages are sent.
        """
        admin_instance = AuthTokenAdmin(AuthToken, site)

        existing_token = AuthToken.objects.first()
        original_access_hash = existing_token.access_token_hash

        request = self.factory.post("/")
        request.user = self.user
        request._messages = []

        # Prepare form data to simulate a change (e.g., updating auth_type)
        updated_data = model_to_dict(existing_token)
        # FIX: Explicitly include required fields (PKs and non-null fields)
        updated_data["user"] = existing_token.user.pk
        updated_data["context"] = "{}"  # JSONField fix
        updated_data["auth_type"] = AUTH_TYPES.HEADER.value

        # Use existing_token as instance for update
        form = admin_instance.form(data=updated_data, instance=existing_token)
        self.assertTrue(form.is_valid(), form.errors)

        with (
            patch("drf_authentify.admin.generate_access_token") as mock_gen_access,
            patch.object(admin_instance, "message_user") as mock_message_user,
        ):

            admin_instance.save_model(request, existing_token, form, change=True)

            self.assertEqual(existing_token.access_token_hash, original_access_hash)

            mock_gen_access.assert_not_called()
            mock_message_user.assert_not_called()
