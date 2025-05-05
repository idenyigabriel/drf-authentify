from django.test import TestCase

from drf_authentify.choices import AUTHTYPE_CHOICES


class AuthTypeChoicesTest(TestCase):
    def test_auth_type_choices_values(self):
        self.assertEqual(AUTHTYPE_CHOICES.HEADER, "header")
        self.assertEqual(AUTHTYPE_CHOICES.COOKIE, "cookie")

    def test_auth_type_choices_labels(self):
        self.assertEqual(AUTHTYPE_CHOICES.HEADER.label, "Header")
        self.assertEqual(AUTHTYPE_CHOICES.COOKIE.label, "Cookie")

    def test_auth_type_choices_iterable(self):
        expected_choices = [("header", "Header"), ("cookie", "Cookie")]
        self.assertEqual(list(AUTHTYPE_CHOICES.choices), expected_choices)

    def test_auth_type_choices_names(self):
        self.assertEqual(AUTHTYPE_CHOICES.names, ["HEADER", "COOKIE"])

    def test_auth_type_choices_members(self):
        self.assertIn(AUTHTYPE_CHOICES.HEADER, list(AUTHTYPE_CHOICES))
        self.assertIn(AUTHTYPE_CHOICES.COOKIE, list(AUTHTYPE_CHOICES))

    def test_auth_type_choices_by_value(self):
        self.assertEqual(AUTHTYPE_CHOICES("header"), AUTHTYPE_CHOICES.HEADER)
        self.assertEqual(AUTHTYPE_CHOICES("cookie"), AUTHTYPE_CHOICES.COOKIE)
