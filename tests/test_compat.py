import sys

from django.test import TestCase


class TypingImportsTests(TestCase):
    def test_typing_imports_module(self):
        if sys.version_info >= (3, 11):
            from typing import Self, TYPE_CHECKING

            expected_module = "typing"
        else:
            from typing_extensions import Self, TYPE_CHECKING

            expected_module = "typing_extensions"

        # Only Self has a meaningful __module__ check
        self.assertEqual(Self.__module__, expected_module)

        # TYPE_CHECKING is always a boolean
        self.assertIsInstance(TYPE_CHECKING, bool)
