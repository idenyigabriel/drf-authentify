import sys

if sys.version_info >= (3, 11):
    from typing import (
        Self,
        Type,
        Union,
        Optional,
        Callable,
        TYPE_CHECKING,
    )  # noqa: F401
else:
    from typing_extensions import (
        Self,
        Type,
        Union,
        Optional,
        Callable,
        TYPE_CHECKING,
    )  # noqa: F401
