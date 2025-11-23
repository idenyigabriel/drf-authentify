import inspect

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

from drf_authentify.compat import Optional, Callable


def load_handler(
    path: str, name: str, required_params: list[str] = ["user", "token", "token_str"]
) -> Optional[Callable]:
    if not path:
        return None

    try:
        handler = import_string(path)
    except ImportError as e:
        raise ImproperlyConfigured(
            f"DRF_AUTHENTIFY setting '{name}'='{path}' cannot be imported: {e}"
        )

    if not callable(handler):
        raise ImproperlyConfigured(
            f"DRF_AUTHENTIFY setting '{name}' must be callable. Got {type(handler).__name__}."
        )

    # Inspect parameters
    sig = inspect.signature(handler)
    params = sig.parameters
    param_names = list(params.keys())

    # Check minimum required parameters
    for i, param_name in enumerate(required_params):
        if i >= len(param_names):
            raise ImproperlyConfigured(
                _(
                    f"{name or 'Handler'} '{path}' must accept at least {len(required_params)} "
                    f"parameters: {', '.join(required_params)}"
                )
            )

    return handler
