from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final


class SortOrder(str, Enum):
    ASC: Final = "ASC"
    DESC: Final = "DESC"
