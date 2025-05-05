from drf_authentify.settings import authentify_settings


class ContextParams:
    def __init__(self, data):
        self._data = data
        self._strict = authentify_settings.STRICT_CONTEXT_PARAMS_ACCESS

    def __getattr__(self, key):
        try:
            return self._data[key]
        except KeyError:
            if not self._strict:
                return None
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{key}'")
