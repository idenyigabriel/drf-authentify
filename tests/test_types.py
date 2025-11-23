from unittest.mock import MagicMock

from django.test import SimpleTestCase

from drf_authentify.types import IssuedTokens


class IssuedTokensTests(SimpleTestCase):
    def setUp(self):
        # Create a mock object to represent the TokenType model instance
        self.mock_token_instance = MagicMock(spec=["__class__"])
        self.mock_token_instance.__class__.__name__ = "TokenType"

        self.issued_tokens = IssuedTokens(
            access_token="access.token.string",
            refresh_token="refresh.token.string",
            token_instance=self.mock_token_instance,
        )

    def test_creation_and_attributes(self):
        self.assertEqual(self.issued_tokens.access_token, "access.token.string")
        self.assertEqual(self.issued_tokens.refresh_token, "refresh.token.string")
        self.assertIs(self.issued_tokens.token_instance, self.mock_token_instance)

    def test_immutability(self):
        with self.assertRaises(AttributeError):
            self.issued_tokens.access_token = "new.access.token"

        with self.assertRaises(AttributeError):
            del self.issued_tokens.refresh_token

    def test_representation(self):
        expected_start = "IssuedTokens(access_token='access.token.string'"
        self.assertTrue(str(self.issued_tokens).startswith(expected_start))
