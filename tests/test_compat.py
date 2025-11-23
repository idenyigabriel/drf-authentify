import sys
from django.test import TestCase


class TypingImportsTests(TestCase):
    def test_typing_imports_module(self):
        if sys.version_info >= (3, 11):
            from typing import Self, Type, Union, Optional, Callable, TYPE_CHECKING

            expected_module = "typing"
        else:
            from typing_extensions import (
                Self,
                Type,
                Union,
                Optional,
                Callable,
                TYPE_CHECKING,
            )

            expected_module = "typing_extensions"

        # Check that all symbols are from the correct module
        for symbol in [Self, Type, Union, Optional, Callable]:
            self.assertEqual(symbol.__module__, expected_module)

        # TYPE_CHECKING is a boolean constant, so just check its type
        self.assertIsInstance(TYPE_CHECKING, bool)
