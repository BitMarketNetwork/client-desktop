from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Final, Iterable


class SortOrder(str, Enum):
    ASC: Final = "ASC"
    DESC: Final = "DESC"


class Query(NotImplementedInstance):
    @staticmethod
    def join(source: Iterable[str]) -> str:
        return ", ".join(source)
