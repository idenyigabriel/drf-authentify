from unittest.mock import patch

from django.test import SimpleTestCase

from drf_authentify.contexts import ContextParams


class ContextParamsTests(SimpleTestCase):
    def setUp(self):
        # Patch authentify_settings for isolation
        patcher = patch("drf_authentify.contexts.authentify_settings")
        self.mock_settings = patcher.start()
        self.addCleanup(patcher.stop)

        # Base data for contexts
        self.data = {"user_id": 1, "is_authenticated": True}

    def test_initialization_requires_dict(self):
        invalid_inputs = ["a string", 123, [1, 2, 3], None]
        for data in invalid_inputs:
            with self.subTest(data=data):
                with self.assertRaisesRegex(TypeError, "expects a dict, got"):
                    ContextParams(data)

    def test_setattr_raises_type_error(self):
        context = ContextParams(self.data)
        with self.assertRaisesRegex(TypeError, "object is read-only"):
            context.new_key = "value"

    def test_delattr_raises_type_error(self):
        context = ContextParams(self.data)
        with self.assertRaisesRegex(TypeError, "object is read-only"):
            del context.user_id

    def test_access_existing_attribute(self):
        self.mock_settings.STRICT_CONTEXT_ACCESS = True
        context = ContextParams(self.data)

        self.assertEqual(context.user_id, 1)
        self.assertTrue(context.is_authenticated)

    def test_strict_mode_raises_attribute_error(self):
        self.mock_settings.STRICT_CONTEXT_ACCESS = True
        context = ContextParams(self.data)

        with self.assertRaisesRegex(
            AttributeError, "'ContextParams' object has no attribute 'missing_key'"
        ):
            _ = context.missing_key

    def test_lenient_mode_returns_none(self):
        self.mock_settings.STRICT_CONTEXT_ACCESS = False
        context = ContextParams(self.data)

        self.assertIsNone(context.missing_key)

    def test_repr_output(self):
        self.mock_settings.STRICT_CONTEXT_ACCESS = True
        context = ContextParams(self.data)

        expected_repr_start = (
            "ContextParams(strict=True, keys=['user_id', 'is_authenticated'])"
        )
        self.assertEqual(context.__repr__(), expected_repr_start)
