import inspect
from unittest import TestCase, mock

from django.core.exceptions import ImproperlyConfigured

from drf_authentify.utils.imports import load_handler


# --- Mock Handler Functions ---
# Used to simulate successfully imported functions with different signatures


def success_handler(user, token, token_str):
    """Handler with the exact required parameters."""
    return user, token, token_str


def extra_args_handler(user, token, token_str, request=None):
    """Handler with more than the required parameters."""
    return user, token, token_str


def fewer_args_handler(user, token):
    """Handler with fewer than the required parameters (missing token_str)."""
    return user, token


# Not callable mock (e.g., a constant or object)
NOT_CALLABLE = 12345


class LoadHandlerTests(TestCase):
    # Default required parameters for most handlers
    REQUIRED_PARAMS = ["user", "token", "token_str"]
    HANDLER_NAME = "TEST_HANDLER"

    # Mock the module path for clean testing
    MOCK_PATH = "some.module.path"

    def test_load_handler_no_path(self):
        """Test that None is returned if the path is empty."""
        self.assertIsNone(load_handler(None, self.HANDLER_NAME, self.REQUIRED_PARAMS))
        self.assertIsNone(load_handler("", self.HANDLER_NAME, self.REQUIRED_PARAMS))

    @mock.patch("drf_authentify.utils.imports.import_string")
    def test_load_handler_import_error(self, mock_import_string):
        """Test that ImproperlyConfigured is raised on ImportError."""
        mock_import_string.side_effect = ImportError("Module not found")

        # Fix: Ensure the regex matches the full exception message, including "DRF_AUTHENTIFY setting"
        expected_regex = r"^DRF_AUTHENTIFY setting 'TEST_HANDLER'='some\.module\.path' cannot be imported: Module not found$"
        with self.assertRaisesRegex(ImproperlyConfigured, expected_regex):
            load_handler(self.MOCK_PATH, self.HANDLER_NAME, self.REQUIRED_PARAMS)

    @mock.patch("drf_authentify.utils.imports.import_string", return_value=NOT_CALLABLE)
    def test_load_handler_not_callable(self, mock_import_string):
        """Test that ImproperlyConfigured is raised if the imported object is not callable."""
        # Fix: Ensure the regex matches the full exception message and the trailing period.
        expected_regex = (
            r"^DRF_AUTHENTIFY setting 'TEST_HANDLER' must be callable\. Got int\.$"
        )
        with self.assertRaisesRegex(ImproperlyConfigured, expected_regex):
            load_handler(self.MOCK_PATH, self.HANDLER_NAME, self.REQUIRED_PARAMS)

    @mock.patch(
        "drf_authentify.utils.imports.import_string", return_value=fewer_args_handler
    )
    def test_load_handler_too_few_parameters(self, mock_import_string):
        """Test that ImproperlyConfigured is raised if the function signature is missing required arguments."""
        expected_regex_fragment = (
            r"TEST_HANDLER 'some\.module\.path' must accept at least 3 "
            r"parameters: user, token, token_str"
        )
        with self.assertRaisesRegex(ImproperlyConfigured, expected_regex_fragment):
            load_handler(self.MOCK_PATH, self.HANDLER_NAME, self.REQUIRED_PARAMS)

    @mock.patch(
        "drf_authentify.utils.imports.import_string", return_value=success_handler
    )
    def test_load_handler_exact_parameters_success(self, mock_import_string):
        """Test successful loading when handler has the exact required signature."""
        handler = load_handler(self.MOCK_PATH, self.HANDLER_NAME, self.REQUIRED_PARAMS)
        self.assertEqual(handler, success_handler)
        self.assertTrue(callable(handler))

        # Verify the signature match was checked
        sig = inspect.signature(handler)
        self.assertEqual(list(sig.parameters.keys()), self.REQUIRED_PARAMS)

    @mock.patch(
        "drf_authentify.utils.imports.import_string", return_value=extra_args_handler
    )
    def test_load_handler_extra_parameters_success(self, mock_import_string):
        """Test successful loading when handler has more than the required arguments."""
        handler = load_handler(self.MOCK_PATH, self.HANDLER_NAME, self.REQUIRED_PARAMS)
        self.assertEqual(handler, extra_args_handler)

        # Verify it still passes because the first N parameters match the required ones
        sig = inspect.signature(handler)
        self.assertTrue(all(req in sig.parameters for req in self.REQUIRED_PARAMS))

    @mock.patch(
        "drf_authentify.utils.imports.import_string", return_value=success_handler
    )
    def test_load_handler_custom_required_parameters(self, mock_import_string):
        """Test successful loading with a custom list of required parameters."""
        custom_params = ["user", "token", "token_str"]
        handler = load_handler(self.MOCK_PATH, self.HANDLER_NAME, custom_params)
        self.assertEqual(handler, success_handler)

        # Test a case where the required params are fewer (it should still pass since the function has the args)
        custom_params_fewer = ["user", "token"]
        handler = load_handler(self.MOCK_PATH, self.HANDLER_NAME, custom_params_fewer)
        self.assertEqual(handler, success_handler)
