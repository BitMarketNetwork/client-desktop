from __future__ import annotations

from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Sequence

from ...utils.integer import LittleOrderIntegerConverter

if TYPE_CHECKING:
    from .coin import Coin


class _Script(LittleOrderIntegerConverter):
    Type = Enum
    OpCode = IntEnum

    @classmethod
    def scriptToBytes(cls, opcode_list: Sequence[int, bytes]) -> bytes | None:
        try:
            return b"".join(
                cls.integerToBytes(c, 1) if isinstance(c, int) else c
                for c in opcode_list
            )
        except TypeError:
            return None

    @classmethod
    def integerToVarInt(cls, value: int) -> bytes | None:
        if value < 0xFD:
            prefix = b""
            length = 1
        elif value <= 0xFFFF:
            prefix = b"\xfd"
            length = 2
        elif value <= 0xFFFFFFFF:
            prefix = b"\xfe"
            length = 4
        elif value <= 0xFFFFFFFFFFFFFFFF:
            prefix = b"\xff"
            length = 8
        else:
            return None

        value = cls.integerToBytes(value, length)
        return (prefix + value) if value is not None else None

    @classmethod
    def integerFromVarInt(cls, value: bytes) -> int | None:
        if len(value) == 1:
            value = cls.integerFromBytes(value)
            return value if value < 0xFD else None

        if len(value) == 3:
            prefix = b"\xfd"
        elif len(value) == 5:
            prefix = b"\xfe"
        elif len(value) == 9:
            prefix = b"\xff"
        else:
            return None

        return cls.integerFromBytes(value[1:]) if value[0] == prefix else None

    @classmethod
    def addressToScript(
        cls, address: Coin.Address, type_: _Script.Type | None = None
    ) -> bytes | None:
        raise NotImplementedError

    @classmethod
    def pushData(cls, data: bytes) -> bytes | None:
        raise NotImplementedError
