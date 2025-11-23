from django.db import models
from django.test import SimpleTestCase

from drf_authentify.choices import AUTH_TYPES


class AuthTypesChoicesTests(SimpleTestCase):
    def test_member_attributes(self):
        self.assertEqual(AUTH_TYPES.HEADER, "header")
        self.assertEqual(AUTH_TYPES.COOKIE, "cookie")

    def test_database_values(self):
        expected_values = ["header", "cookie"]
        self.assertEqual(list(AUTH_TYPES.values), expected_values)

    def test_human_readable_labels(self):
        expected_labels = ["Header", "Cookie"]
        self.assertEqual(list(AUTH_TYPES.labels), expected_labels)

    def test_choices_tuple(self):
        expected_choices = [("header", "Header"), ("cookie", "Cookie")]
        self.assertEqual(list(AUTH_TYPES.choices), expected_choices)

    def test_parent_instance(self):
        self.assertTrue(issubclass(AUTH_TYPES, models.TextChoices))
