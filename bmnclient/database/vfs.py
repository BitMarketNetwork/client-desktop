from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Vfs:
    def open(self, path: str, flags: int) -> Any:
        pass
