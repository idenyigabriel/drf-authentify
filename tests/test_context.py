from django.test import TestCase

from drf_authentify.settings import authentify_settings
from drf_authentify.context import ContextParams  # Replace with the actual import path


class ContextParamsTest(TestCase):
    def setUp(self):
        self.initial_strict_setting = authentify_settings.STRICT_CONTEXT_PARAMS_ACCESS

    def tearDown(self):
        authentify_settings.STRICT_CONTEXT_PARAMS_ACCESS = self.initial_strict_setting

    def test_access_existing_attribute(self):
        data = {"user_id": 123, "role": "admin"}
        context_params = ContextParams(data)
        self.assertEqual(context_params.user_id, 123)
        self.assertEqual(context_params.role, "admin")

    def test_access_non_existing_attribute_strict_mode(self):
        authentify_settings.STRICT_CONTEXT_PARAMS_ACCESS = True
        data = {"user_id": 123}
        context_params = ContextParams(data)
        with self.assertRaises(AttributeError) as cm:
            _ = context_params.username
        self.assertEqual(str(cm.exception), "ContextParams has no attribute 'username'")

    def test_access_non_existing_attribute_non_strict_mode(self):
        authentify_settings.STRICT_CONTEXT_PARAMS_ACCESS = False
        data = {"user_id": 123}
        context_params = ContextParams(data)
        self.assertIsNone(context_params.username)

    def test_empty_data_strict_mode(self):
        authentify_settings.STRICT_CONTEXT_PARAMS_ACCESS = True
        context_params = ContextParams({})
        with self.assertRaises(AttributeError):
            _ = context_params.some_key

    def test_empty_data_non_strict_mode(self):
        authentify_settings.STRICT_CONTEXT_PARAMS_ACCESS = False
        context_params = ContextParams({})
        self.assertIsNone(context_params.some_key)

    def test_data_with_none_value(self):
        data = {"status": None}
        context_params = ContextParams(data)
        self.assertIsNone(context_params.status)

    def test_different_data_types(self):
        data = {"count": 5, "is_active": True, "message": "hello"}
        context_params = ContextParams(data)
        self.assertEqual(context_params.count, 5)
        self.assertTrue(context_params.is_active)
        self.assertEqual(context_params.message, "hello")
