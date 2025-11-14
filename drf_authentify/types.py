from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from drf_authentify.models import TokenType


@dataclass(frozen=True)
class GeneratedToken:
    token: str
    refresh: str
    instance: "TokenType"
