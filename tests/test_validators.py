from django.test import TestCase
from django.core.exceptions import ValidationError

from drf_authentify.validators import validate_context


class ContextValidatorTests(TestCase):
    def test_valid_context(self):
        try:
            validate_context({"key": "value", "number": 42})
        except ValidationError:
            self.fail(
                "validate_context raised ValidationError unexpectedly for a dict."
            )

    def test_invalid_context_raises_validation_error(self):
        invalid_values = ["a string", 12345, [1, 2, 3], None, (1, 2), True]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaisesMessage(
                    ValidationError, "Context must be a dictionary."
                ):
                    validate_context(value)
