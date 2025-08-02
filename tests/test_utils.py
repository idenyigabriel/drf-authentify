from unittest.mock import patch
from django.test import TestCase

from drf_authentify.utils import generate_token  # adjust path as needed
from drf_authentify.settings import authentify_settings


class TestGenerateToken(TestCase):
    def test_generate_token_success_first_try(self):
        """It should return a token when no collision occurs."""
        with patch("drf_authentify.models.AuthToken.objects.filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            token = generate_token()
            self.assertIsInstance(token, str)
            self.assertGreater(len(token), 30)  # Should be ~43 chars

    def test_generate_token_with_retries(self):
        """It should retry on collision and eventually succeed."""
        # Simulate collision on first 2 attempts, success on 3rd
        exists_side_effects = [True, True, False]
        with patch("drf_authentify.models.AuthToken.objects.filter") as mock_filter:
            mock_filter.return_value.exists.side_effect = exists_side_effects
            token = generate_token()
            self.assertIsInstance(token, str)

            self.assertEqual(mock_filter.return_value.exists.call_count, 3)

    def test_generate_token_raises_after_max_attempts(self):
        """It should raise RuntimeError after all attempts fail due to collisions."""
        max_attempts = authentify_settings.MAX_TOKEN_CREATION_ATTEMPTS
        with patch("drf_authentify.models.AuthToken.objects.filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True  # Always collides

            with self.assertRaises(RuntimeError) as ctx:
                generate_token()

            self.assertIn("Could not generate a unique token", str(ctx.exception))
            self.assertEqual(mock_filter.return_value.exists.call_count, max_attempts)
