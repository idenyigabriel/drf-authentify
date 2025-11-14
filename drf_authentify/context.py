from drf_authentify.settings import authentify_settings


class ContextParams:
    """
    Wraps a dictionary to allow attribute-style access with optional strict mode.
    """

    def __init__(self, data):
        if not isinstance(data, dict):
            raise TypeError(f"ContextParams expects a dict, got {type(data).__name__}")

        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_strict", authentify_settings.STRICT_CONTEXT_ACCESS)

    def __getattr__(self, key):
        # Avoid treating private/internals as context keys
        if key.startswith("_"):
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{key}'")

        if key in self._data:
            return self._data[key]

        if self._strict:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{key}'")

        return None

    def __setattr__(self, key, value):
        # Disallow overwriting internals except during init or explicit override
        if key in ("_data", "_strict"):
            object.__setattr__(self, key, value)
            return

        if key.startswith("_"):
            raise AttributeError(f"Cannot modify internal attribute '{key}'")

        # Store user values into wrapped dictionary
        self._data[key] = value

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data})"
