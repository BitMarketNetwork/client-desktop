from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Final, Iterable, Tuple
    from .column import Column


class SortOrder(str, Enum):
    ASC: Final = "ASC"
    DESC: Final = "DESC"


class Query(NotImplementedInstance):
    @staticmethod
    def join(source: Iterable[str]) -> str:
        return ", ".join(source)

    @classmethod
    def joinSortOrder(cls, source: Iterable[Tuple[Column, SortOrder]]) -> str:
        return cls.join(f"{s[0].identifier} {s[1]}" for s in source)

    @classmethod
    def qmark(cls, count: int) -> str:
        return cls.join("?" * count)
