from django.test import TestCase
from django.core.exceptions import ValidationError

from drf_authentify.validators import validate_dict


class ValidateDictOrEmptyTests(TestCase):
    def test_valid_dictionary(self):
        self.assertIsNone(validate_dict({"key": "value"}))

    def test_empty_dictionary(self):
        self.assertIsNone(validate_dict({}))

    def test_none_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_dict(None)
        self.assertEqual(context.exception.message, "Context must be a dictionary.")

    def test_string_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_dict("not a dict")
        self.assertEqual(context.exception.message, "Context must be a dictionary.")

    def test_list_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_dict([1, 2, 3])
        self.assertEqual(context.exception.message, "Context must be a dictionary.")

    def test_set_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_dict({1, 2, 3})
        self.assertEqual(context.exception.message, "Context must be a dictionary.")

    def test_tuple_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_dict((1, 2, 3))
        self.assertEqual(context.exception.message, "Context must be a dictionary.")

    def test_integer_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_dict(123)
        self.assertEqual(context.exception.message, "Context must be a dictionary.")

    def test_boolean_value(self):
        with self.assertRaises(ValidationError) as context:
            validate_dict(True)
        self.assertEqual(context.exception.message, "Context must be a dictionary.")
