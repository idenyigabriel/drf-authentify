import hashlib
from unittest.mock import patch

from django.test import SimpleTestCase

from drf_authentify.utils.tokens import (
    _hash_token,
    _generate_token,
    hash_token_string,
    generate_access_token,
    generate_refresh_token,
)


class TokenUtilityTests(SimpleTestCase):
    def setUp(self):
        # Start the patch and store the mock object
        patcher = patch("drf_authentify.utils.tokens.authentify_settings")
        self.mock_settings = patcher.start()
        self.addCleanup(patcher.stop)  # Automatically stop the patch after the test

        # Configure the mock
        self.mock_settings.SECURE_HASH_ALGORITHM = "sha256"
        self.test_token = "test_raw_token_value"
        self.expected_sha256_hash = hashlib.sha256(
            self.test_token.encode("utf-8")
        ).hexdigest()

    def test_hash_token_consistency(self):
        result = _hash_token(self.test_token)
        self.assertEqual(result, self.expected_sha256_hash)

    def test_hash_token_algorithm_change(self):
        self.mock_settings.SECURE_HASH_ALGORITHM = "sha512"
        expected_hash = hashlib.sha512(self.test_token.encode("utf-8")).hexdigest()

        result = _hash_token(self.test_token)
        self.assertEqual(result, expected_hash)
        self.assertNotEqual(result, self.expected_sha256_hash)

    @patch("drf_authentify.utils.tokens.secrets")
    def test_generate_token_structure(self, mock_secrets):
        # Mock secrets to return a predictable raw token for testing
        mock_secrets.token_urlsafe.return_value = self.test_token

        raw, hashed = _generate_token(16)

        self.assertEqual(raw, self.test_token)
        self.assertEqual(hashed, self.expected_sha256_hash)
        mock_secrets.token_urlsafe.assert_called_once_with(16)

    def test_hash_token_string_public(self):
        result = hash_token_string(self.test_token)
        self.assertEqual(result, self.expected_sha256_hash)

    def test_generate_access_token(self):
        raw, hashed = generate_access_token()

        # Check that the raw token is approximately 32 * 4/3 characters long
        self.assertTrue(len(raw) >= 42)  # 32 bytes B64 is 42.66 characters
        self.assertEqual(len(hashed), 64)  # SHA256 is 64 hex characters
        self.assertNotEqual(raw, hashed)

    def test_generate_refresh_token(self):
        raw, hashed = generate_refresh_token()

        # Check that the raw token is approximately 48 * 4/3 characters long
        self.assertTrue(len(raw) >= 64)  # 48 bytes B64 is 64 characters
        self.assertEqual(len(hashed), 64)  # SHA256 is 64 hex characters
        self.assertNotEqual(raw, hashed)

    def test_generated_tokens_are_different(self):
        raw1, _ = generate_access_token()
        raw2, _ = generate_access_token()
        self.assertNotEqual(raw1, raw2)
