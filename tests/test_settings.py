from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from drf_authentify.settings import (
    DEFAULTS,
    APISettings,
    reload_authentify_settings,
    validate_authentify_settings,
)


class SettingsValidationTests(TestCase):
    def setUp(self):
        # Ensure we start with defaults before each test
        # We use reload_authentify_settings with None to reset to DEFAULTS
        reload_authentify_settings(setting="DRF_AUTHENTIFY", value=None)

    def _test_invalid_setting(
        self,
        setting_key,
        setting_value,
        expected_regex,
        use_defaults=True,
        custom_data=None,
    ):
        """
        Helper function to test settings validation failures by creating
        a new APISettings instance and running validation on it.
        """
        if use_defaults:
            invalid_settings_dict = DEFAULTS.copy()
            invalid_settings_dict.update({setting_key: setting_value})
        elif custom_data:
            invalid_settings_dict = custom_data

        # 1. Create a temporary settings object with the invalid data
        temp_settings = APISettings(invalid_settings_dict, DEFAULTS)

        # 2. Patch the global authentify_settings object temporarily
        with patch("drf_authentify.settings.authentify_settings", temp_settings):
            with self.assertRaisesRegex(ImproperlyConfigured, expected_regex):
                # 3. Run the validation function against the temporary settings
                validate_authentify_settings()

    ## --- Validation Success (Defaults & Overrides) ---

    def test_default_settings_are_valid(self):
        """Ensures the built-in DEFAULTS pass validation."""
        try:
            validate_authentify_settings()
        except ImproperlyConfigured as e:
            self.fail(f"Default settings failed validation: {e}")

    def test_successful_custom_settings(self):
        """Ensures multiple valid overrides are applied correctly and defaults are maintained."""
        custom_settings = {
            "TOKEN_TTL": timedelta(minutes=5),
            "SECURE_HASH_ALGORITHM": "sha512",
            "AUTH_HEADER_PREFIXES": ["JWT"],
            "STRICT_CONTEXT_ACCESS": True,
        }

        # Manually create the APISettings object with the custom data
        test_settings = APISettings(custom_settings, DEFAULTS)

        # 1. Verify all overridden values are used
        self.assertEqual(test_settings.TOKEN_TTL, timedelta(minutes=5))
        self.assertEqual(test_settings.SECURE_HASH_ALGORITHM, "sha512")
        self.assertTrue(test_settings.STRICT_CONTEXT_ACCESS)

        # 2. Verify an UN-overridden default value is still present
        self.assertEqual(
            test_settings.ENFORCE_SINGLE_LOGIN, DEFAULTS["ENFORCE_SINGLE_LOGIN"]
        )

    ## --- Validation Failures (Using the Helper) ---

    def test_invalid_type_raises_exception(self):
        """Ensures a setting with an incorrect type raises ImproperlyConfigured."""
        self._test_invalid_setting(
            "TOKEN_TTL",
            "not a timedelta",
            r"Invalid type for DRF_AUTHENTIFY setting 'TOKEN_TTL': expected \(<class 'datetime.timedelta'>, <class 'NoneType'>\), got str",
        )

    def test_empty_list_raises_exception(self):
        """Ensures empty list settings (e.g., AUTH_COOKIE_NAMES) are rejected."""
        self._test_invalid_setting(
            "AUTH_COOKIE_NAMES",
            [],
            r"DRF_AUTHENTIFY setting AUTH_COOKIE_NAMES cannot be an empty list.",
        )

    def test_non_string_in_list_raises_exception(self):
        """Ensures lists containing non-strings are rejected."""
        self._test_invalid_setting(
            "AUTH_HEADER_PREFIXES",
            [123],
            r"All items in DRF_AUTHENTIFY setting 'AUTH_HEADER_PREFIXES' must be strings.",
        )

    def test_invalid_hash_algorithm_raises_exception(self):
        """Ensures SECURE_HASH_ALGORITHM must be a valid hashlib algorithm."""
        self._test_invalid_setting(
            "SECURE_HASH_ALGORITHM",
            "invalid_hash_algo",
            r"'invalid_hash_algo' is not found in hashlib.",
        )

    def test_non_positive_ttl_raises_exception(self):
        """Ensures TOKEN_TTL and REFRESH_TOKEN_TTL must be positive."""
        self._test_invalid_setting(
            "TOKEN_TTL",
            timedelta(seconds=0),
            r"DRF_AUTHENTIFY setting 'TOKEN_TTL' must be positive.",
        )

    def test_negative_interval_raises_exception(self):
        """Ensures AUTO_REFRESH_INTERVAL cannot be negative."""
        self._test_invalid_setting(
            "AUTO_REFRESH_INTERVAL",
            timedelta(seconds=-1),
            r"DRF_AUTHENTIFY setting 'AUTO_REFRESH_INTERVAL' cannot be negative",
        )

    def test_refresh_ttl_not_greater_than_token_ttl_raises_exception(self):
        """Ensures REFRESH_TOKEN_TTL must be strictly greater than TOKEN_TTL."""
        custom_data = DEFAULTS.copy()
        custom_data.update(
            {
                "TOKEN_TTL": timedelta(hours=10),
                "REFRESH_TOKEN_TTL": timedelta(hours=10),  # Equal, should fail
            }
        )
        self._test_invalid_setting(
            setting_key=None,
            setting_value=None,
            expected_regex=r"REFRESH_TOKEN_TTL must be strictly greater than TOKEN_TTL.",
            use_defaults=False,
            custom_data=custom_data,
        )

    def test_auto_refresh_missing_dependency_raises_exception(self):
        """Ensures required settings for AUTO_REFRESH are checked."""
        custom_data = DEFAULTS.copy()
        custom_data.update(
            {
                "AUTO_REFRESH": True,
                # Dependencies set to None to trigger failure
                "REFRESH_TOKEN_TTL": None,
                "AUTO_REFRESH_MAX_TTL": None,
                "AUTO_REFRESH_INTERVAL": None,
            }
        )
        self._test_invalid_setting(
            setting_key=None,
            setting_value=None,
            expected_regex=r"AUTO_REFRESH cannot be enabled without the following: REFRESH_TOKEN_TTL, AUTO_REFRESH_MAX_TTL, AUTO_REFRESH_INTERVAL",
            use_defaults=False,
            custom_data=custom_data,
        )
