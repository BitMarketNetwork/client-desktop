# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final, Optional


class AbstractIntegerConverter:
    _BYTE_ORDER = ""

    @classmethod
    def integerToBytes(cls, value: int, length: int) -> Optional[bytes]:
        try:
            return value.to_bytes(length, cls._BYTE_ORDER)
        except OverflowError:
            return None

    @classmethod
    def integerToAutoBytes(cls, value: int) -> bytes:
        length = (value.bit_length() + 7) // 8 or 1
        # OverflowError impossible
        return value.to_bytes(length, cls._BYTE_ORDER)

    @classmethod
    def integerFromBytes(cls, value: bytes) -> int:
        return int.from_bytes(value, cls._BYTE_ORDER)


class LittleOrderIntegerConverter(AbstractIntegerConverter):
    _BYTE_ORDER: Final = "little"


class BigOrderIntegerConverter(AbstractIntegerConverter):
    _BYTE_ORDER: Final = "big"
