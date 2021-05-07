# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Iterable


def filterNotNone(iterable: Iterable) -> Any:
    for v in iterable:
        if v is not None:
            yield v
