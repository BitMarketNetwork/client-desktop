from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


class AbstractScript:
    _BYTE_ORDER = "little"

    @classmethod
    def integerToBytes(cls, value: int, length) -> Optional[bytes]:
        try:
            return value.to_bytes(length, cls._BYTE_ORDER)
        except OverflowError:
            return None

    @classmethod
    def integerFromBytes(cls, value: bytes) -> int:
        return int.from_bytes(value, cls._BYTE_ORDER)
