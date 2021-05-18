# JOK4
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from ...utils.integer import LittleOrderIntegerConverter

if TYPE_CHECKING:
    from typing import Iterable, Optional
    from .coin import AbstractCoin


class _AbstractScript(LittleOrderIntegerConverter):
    OpCode = IntEnum

    @classmethod
    def scriptToBytes(
            cls,
            opcode_list: Iterable[int, bytes]) -> Optional[bytes]:
        try:
            return b"".join(map(
                lambda v: cls.integerToBytes(v, 1) if isinstance(v, int) else v,
                opcode_list))
        except TypeError:
            return None

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

    @classmethod
    def addressToScript(
            cls,
            address: AbstractCoin.Address,
            type_: Optional[AbstractCoin.Address.Type] = None) \
            -> Optional[bytes]:
        raise NotImplementedError
