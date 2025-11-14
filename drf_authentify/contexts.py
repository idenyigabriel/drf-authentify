from drf_authentify.settings import authentify_settings


class ContextParams:
    def __init__(self, data: dict):
        if not isinstance(data, dict):
            raise TypeError(
                f"{self.__class__.__name__} expects a dict, got {type(data).__name__}"
            )

        # Internal storage
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_strict", authentify_settings.STRICT_CONTEXT_ACCESS)

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        if self._strict:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        return None

    def __setattr__(self, name, value):
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def __delattr__(self, name):
        raise TypeError(f"'{self.__class__.__name__}' object is read-only")

    def __repr__(self):
        return f"{self.__class__.__name__}(strict={self._strict}, keys={list(self._data.keys())})"
