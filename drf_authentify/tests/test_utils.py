import secrets
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from drf_authentify.choices import AUTH
from drf_authentify.models import AuthToken
from drf_authentify.utils import (
    clear_request_tokens,
    delete_request_token,
    clear_expired_tokens,
    clear_user_tokens,
)


class TestUtils(TestCase):
    def setUp(self):
        username = "john.doe"
        email = "john.doe@example.com"
        password = "hunter2"
        self.user = get_user_model().objects.create_user(username, email, password)

    def tearDown(self) -> None:
        self.user.delete()

    def __create_extra_token_data(self, auth, expires: int = 0):
        """utility method for quickly creating extra test token"""
        return AuthToken.objects.create(
            auth=auth,
            user=self.user,
            token=secrets.token_urlsafe(),
            expires_at=timezone.now() + timedelta(seconds=expires),
        )

    def test_clear_user_tokens(self):
        self.__create_extra_token_data(AUTH.TOKEN, expires=2000)
        self.__create_extra_token_data(AUTH.COOKIE, expires=2000)
        self.__create_extra_token_data(AUTH.TOKEN)
        self.__create_extra_token_data(AUTH.COOKIE)

        self.assertGreater(AuthToken.objects.count(), 0)
        clear_user_tokens(self.user)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_delete_request_token(self):
        token = self.__create_extra_token_data(AUTH.TOKEN, expires=2000)
        request = APIRequestFactory()
        request.user = self.user
        request.auth = token.token

        self.assertEqual(AuthToken.objects.count(), 1)
        delete_request_token(request)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_clear_request_tokens(self):
        token = self.__create_extra_token_data(AUTH.TOKEN, expires=2000)
        self.__create_extra_token_data(AUTH.TOKEN, expires=2000)
        self.__create_extra_token_data(AUTH.TOKEN, expires=2000)
        self.__create_extra_token_data(AUTH.TOKEN, expires=2000)
        request = APIRequestFactory()
        request.user = self.user
        request.auth = token

        self.assertEqual(AuthToken.objects.count(), 4)
        clear_request_tokens(request)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_clear_expired_tokens(self):
        self.__create_extra_token_data(AUTH.TOKEN, expires=0)
        self.__create_extra_token_data(AUTH.TOKEN, expires=0)

        self.assertEqual(AuthToken.objects.count(), 2)
        clear_expired_tokens()
        self.assertEqual(AuthToken.objects.count(), 0)
