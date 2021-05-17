from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional
    from .coin import AbstractCoin


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

    @classmethod
    def integerToVarInt(cls, value: int) -> Optional[bytes]:
        if value < 0xfd:
            prefix = b''
            length = 1
        elif value <= 0xffff:
            prefix = b'\xfd'
            length = 2
        elif value <= 0xffffffff:
            prefix = b'\xfe'
            length = 4
        elif value <= 0xffffffffffffffff:
            prefix = b'\xff'
            length = 8
        else:
            return None

        value = cls.integerToBytes(value, length)
        return (prefix + value) if value is not None else None

    @classmethod
    def integerFromVarInt(cls, value: bytes) -> Optional[int]:
        if len(value) == 1:
            value = cls.integerFromBytes(value)
            return value if value < 0xfd else None

        if len(value) == 3:
            prefix = b'\xfd'
        elif len(value) == 5:
            prefix = b'\xfe'
        elif len(value) == 9:
            prefix = b'\xff'
        else:
            return None

        return cls.integerFromBytes(value[1:]) if value[0] == prefix else None
