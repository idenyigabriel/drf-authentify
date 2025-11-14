import sys

if sys.version_info >= (3, 11):
    from typing import Self, Type, TYPE_CHECKING
else:
    from typing_extensions import Self, Type, TYPE_CHECKING
