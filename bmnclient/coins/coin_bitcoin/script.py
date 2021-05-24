# JOK4
from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from ..abstract.coin import AbstractCoin

if TYPE_CHECKING:
    from typing import Final, Optional
    from . import Bitcoin


class _BitcoinScript(AbstractCoin.Script):
    class Type(AbstractCoin.Script.Type):
        NONE = auto()
        P2PK = auto()
        P2PKH = auto()
        P2SH = auto()
        P2SH_P2WPKH = auto()
        P2WPKH = auto()
        P2WSH = auto()

    class OpCode(AbstractCoin.Script.OpCode):
        OP_0: Final = 0x00
        OP_PUSHDATA1: Final = 0x4c
        OP_PUSHDATA2: Final = 0x4d
        OP_PUSHDATA4: Final = 0x4e
        OP_RETURN: Final = 0x6a
        OP_DUP: Final = 0x76
        OP_EQUAL: Final = 0x87
        OP_EQUALVERIFY: Final = 0x88
        OP_HASH160: Final = 0xa9
        OP_CHECKSIG: Final = 0xac

    @classmethod
    def addressToScript(
            cls,
            address: Bitcoin.Address,
            type_: Optional[Bitcoin.Address.Type] = None) -> Optional[bytes]:
        address_hash = address.hash
        if not (0 < len(address_hash) < 0xff):
            return None

        if type_ is None:
            type_ = address.type

        if type_ == address.Type.PUBKEY:
            print("JJJJJ")
            script = (
                len(address.publicKey.data),
                address.publicKey.data,
                cls.OpCode.OP_CHECKSIG
            )
        elif type_ == address.Type.PUBKEY_HASH:
            if len(address_hash) != 0x14:
                return None
            script = (
                cls.OpCode.OP_DUP,
                cls.OpCode.OP_HASH160,
                len(address_hash),
                address_hash,
                cls.OpCode.OP_EQUALVERIFY,
                cls.OpCode.OP_CHECKSIG
            )
        elif type_ == address.Type.SCRIPT_HASH:
            if len(address_hash) != 0x14:
                return None
            script = (
                cls.OpCode.OP_HASH160,
                len(address_hash),
                address_hash,
                cls.OpCode.OP_EQUAL
            )
        elif type_ in (
                address.Type.WITNESS_V0_KEY_HASH,
                address.Type.WITNESS_V0_SCRIPT_HASH
        ):
            script = (
                cls.OpCode.OP_0,
                len(address_hash),
                address_hash
            )
        else:
            return None

        return cls.scriptToBytes(script)

    @classmethod
    def pushData(cls, data: bytes) -> Optional[bytes]:
        length = len(data)
        if length <= 0x4b:
            script = (
                cls.integerToBytes(length, 1),
                data)
        elif length <= 0xff:
            script = (
                cls.OpCode.OP_PUSHDATA1,
                cls.integerToBytes(length, 1),
                data)
        elif length <= 0xffff:
            script = (
                cls.OpCode.OP_PUSHDATA2,
                cls.integerToBytes(length, 2),
                data)
        elif length <= 0xffffffff:
            script = (
                cls.OpCode.OP_PUSHDATA4,
                cls.integerToBytes(length, 4),
                data)
        else:
            return None
        return cls.scriptToBytes(script)
