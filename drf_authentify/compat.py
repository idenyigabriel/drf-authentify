import sys

if sys.version_info >= (3, 11):
    from typing import Self, Type, Union, TYPE_CHECKING
else:
    from typing_extensions import Self, Type, Union, TYPE_CHECKING
