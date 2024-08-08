import json
import secrets
from django.db import models
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from drf_authentify.choices import AUTH
from drf_authentify.models import AuthToken
from drf_authentify.settings import authentify_settings


class AuthTokenModelFieldsTestCase(TestCase):
    def setUp(self):
        username = "john.doe"
        email = "john.doe@example.com"
        password = "hunter2"
        self.user = get_user_model().objects.create_user(username, email, password)

        self.token = AuthToken.objects.create(
            user=self.user,
            auth=AUTH.TOKEN,
            expires_at=timezone.now(),
            token=secrets.token_bytes(),
        )

    def tearDown(self) -> None:
        self.user.delete()
        self.token.delete()

    def test_token_field(self):
        self.assertFalse(self.token._meta.get_field("token").null)
        self.assertFalse(self.token._meta.get_field("token").blank)
        self.assertTrue(self.token._meta.get_field("token").unique)
        self.assertTrue(self.token._meta.get_field("token").editable)
        self.assertIsNone(self.token._meta.get_field("token").choices)
        self.assertFalse(self.token._meta.get_field("token").is_relation)
        self.assertEqual(self.token._meta.get_field("token").max_length, 255)
        self.assertEqual(self.token._meta.get_field("token").verbose_name, "token")
        self.assertIsInstance(self.token._meta.get_field("token"), models.CharField)

    def test_user_field(self):
        self.assertFalse(self.token._meta.get_field("user").null)
        self.assertFalse(self.token._meta.get_field("user").blank)
        self.assertFalse(self.token._meta.get_field("user").unique)
        self.assertTrue(self.token._meta.get_field("user").editable)
        self.assertIsNone(self.token._meta.get_field("user").choices)
        self.assertTrue(self.token._meta.get_field("user").is_relation)
        self.assertIsNone(self.token._meta.get_field("user").max_length)
        self.assertEqual(self.token._meta.get_field("user").verbose_name, "user")
        self.assertEqual(
            self.token._meta.get_field("user").related_model, get_user_model()
        )

    def test_auth_field(self):
        self.assertFalse(self.token._meta.get_field("auth").null)
        self.assertFalse(self.token._meta.get_field("auth").blank)
        self.assertFalse(self.token._meta.get_field("auth").unique)
        self.assertTrue(self.token._meta.get_field("auth").editable)
        self.assertFalse(self.token._meta.get_field("auth").is_relation)
        self.assertEqual(self.token._meta.get_field("auth").max_length, 6)
        self.assertEqual(self.token._meta.get_field("auth").verbose_name, "auth")
        self.assertEqual(self.token._meta.get_field("auth").choices, AUTH.choices)
        self.assertIsInstance(self.token._meta.get_field("auth"), models.CharField)

    def test_context_field(self):
        self.assertTrue(self.token._meta.get_field("_context").null)
        self.assertTrue(self.token._meta.get_field("_context").blank)
        self.assertFalse(self.token._meta.get_field("_context").unique)
        self.assertTrue(self.token._meta.get_field("_context").editable)
        self.assertIsNone(self.token._meta.get_field("_context").choices)
        self.assertFalse(self.token._meta.get_field("_context").is_relation)
        self.assertIsNone(self.token._meta.get_field("_context").max_length)
        self.assertIsInstance(self.token._meta.get_field("_context"), models.TextField)
        self.assertEqual(self.token._meta.get_field("_context").verbose_name, "context")

    def test_expires_at_field(self):
        self.assertFalse(self.token._meta.get_field("expires_at").null)
        self.assertFalse(self.token._meta.get_field("expires_at").blank)
        self.assertFalse(self.token._meta.get_field("expires_at").unique)
        self.assertTrue(self.token._meta.get_field("expires_at").editable)
        self.assertIsNone(self.token._meta.get_field("expires_at").choices)
        self.assertIsNone(self.token._meta.get_field("expires_at").max_length)
        self.assertFalse(self.token._meta.get_field("expires_at").is_relation)
        self.assertEqual(
            self.token._meta.get_field("expires_at").verbose_name, "expires at"
        )
        self.assertIsInstance(
            self.token._meta.get_field("expires_at"), models.DateTimeField
        )

    def test_created_at_field(self):
        self.assertTrue(self.token._meta.get_field("created_at").blank)
        self.assertFalse(self.token._meta.get_field("created_at").null)
        self.assertFalse(self.token._meta.get_field("created_at").unique)
        self.assertFalse(self.token._meta.get_field("created_at").editable)
        self.assertIsNone(self.token._meta.get_field("created_at").choices)
        self.assertIsNone(self.token._meta.get_field("created_at").max_length)
        self.assertFalse(self.token._meta.get_field("created_at").is_relation)
        self.assertIsInstance(
            self.token._meta.get_field("created_at"), models.DateTimeField
        )
        self.assertEqual(
            self.token._meta.get_field("created_at").verbose_name, "created at"
        )


class TestAuthTokenModelMethods(TestCase):
    def setUp(self):
        username = "john.doe"
        email = "john.doe@example.com"
        password = "hunter2"
        self.user = get_user_model().objects.create_user(username, email, password)

        self.token_context = {"role": "admin"}
        self.token = AuthToken.objects.create(
            user=self.user,
            auth=AUTH.TOKEN,
            expires_at=timezone.now(),
            token=secrets.token_bytes(),
            context=json.dumps(self.token_context),
        )

    def tearDown(self) -> None:
        self.user.delete()
        self.token.delete()

    def __create_extra_token_data(self, auth, expires: int = 0):
        """utility method for quickly creating extra test token"""
        return AuthToken.objects.create(
            auth=auth,
            user=self.user,
            token=secrets.token_urlsafe(),
            expires_at=timezone.now() + timedelta(seconds=expires),
        )

    def test_str_method(self):
        self.assertEqual(self.token.__str__(), f"{self.token.token} : {self.user}")

    def test_cookie_generate_token(self):
        token = AuthToken.generate_cookie_token(self.user, context={"role": "admin"})
        self.assertIsInstance(token, str)

        token_instance = AuthToken.objects.filter(token=token).first()

        self.assertIsInstance(token_instance, AuthToken)
        self.assertEqual(token_instance.user, self.user)
        self.assertEqual(token_instance.auth, AUTH.COOKIE)
        self.assertDictEqual(token_instance.context, {"role": "admin"})

        self.assertAlmostEqual(
            token_instance.expires_at,
            token_instance.created_at
            + timedelta(seconds=authentify_settings.TOKEN_EXPIRATION),
            delta=timedelta(seconds=10),
        )

        token_instance.delete()

    def test_cookie_generate_token_variety(self):
        token = AuthToken.generate_cookie_token(self.user, expires=100)
        self.assertIsInstance(token, str)

        token_instance = AuthToken.objects.filter(token=token).first()

        self.assertIsInstance(token_instance, AuthToken)
        self.assertEqual(token_instance.user, self.user)
        self.assertEqual(token_instance.auth, AUTH.COOKIE)
        self.assertIsNone(token_instance.context)

        self.assertAlmostEqual(
            token_instance.expires_at,
            token_instance.created_at + timedelta(seconds=100),
            delta=timedelta(seconds=10),
        )

        token_instance.delete()

    def test_token_type_generate_token(self):
        token = AuthToken.generate_header_token(self.user, context={"role": "admin"})
        self.assertIsInstance(token, str)

        token_instance = AuthToken.objects.filter(token=token).first()

        self.assertIsInstance(token_instance, AuthToken)
        self.assertEqual(token_instance.user, self.user)
        self.assertEqual(token_instance.auth, AUTH.TOKEN)
        self.assertDictEqual(token_instance.context, {"role": "admin"})

        self.assertAlmostEqual(
            token_instance.expires_at,
            token_instance.created_at
            + timedelta(seconds=authentify_settings.TOKEN_EXPIRATION),
            delta=timedelta(seconds=10),
        )

        token_instance.delete()

    def test_token_type_generate_token_variety(self):
        token = AuthToken.generate_header_token(self.user, expires=1000)
        self.assertIsInstance(token, str)

        token_instance = AuthToken.objects.filter(token=token).first()

        self.assertIsInstance(token_instance, AuthToken)
        self.assertEqual(token_instance.user, self.user)
        self.assertEqual(token_instance.auth, AUTH.TOKEN)
        self.assertIsNone(token_instance.context)

        self.assertAlmostEqual(
            token_instance.expires_at,
            token_instance.created_at + timedelta(seconds=1000),
            delta=timedelta(seconds=10),
        )

        token_instance.delete()

    def test_verify_token(self):
        token1 = self.__create_extra_token_data(AUTH.TOKEN, expires=2000)
        token2 = self.__create_extra_token_data(AUTH.COOKIE, expires=2000)
        token3 = self.__create_extra_token_data(AUTH.TOKEN)
        token4 = self.__create_extra_token_data(AUTH.COOKIE)

        # success
        self.assertIsInstance(
            AuthToken.verify_token(token1.token, AUTH.TOKEN), AuthToken
        )
        self.assertIsInstance(
            AuthToken.verify_token(token2.token, AUTH.COOKIE), AuthToken
        )

        # fails for wrong auth type
        self.assertIsNone(AuthToken.verify_token(token2.token, AUTH.TOKEN))
        self.assertIsNone(AuthToken.verify_token(token1.token, AUTH.COOKIE))

        # fails for being expired
        self.assertIsNone(AuthToken.verify_token(token3.token, AUTH.TOKEN))
        self.assertIsNone(AuthToken.verify_token(token4.token, AUTH.COOKIE))

        token1.delete()
        token2.delete()
        token3.delete()
        token4.delete()
