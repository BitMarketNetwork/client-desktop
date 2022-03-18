from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .tx_io import _Io
from ...utils import DeserializationNotSupportedError, serializable

if TYPE_CHECKING:
    from typing import Final, Optional
    from .coin import Coin


class _MutableIo(_Io):
    _AMOUNT_LENGTH = 0

    def __init__(
            self,
            address: Coin.Address,
            *,
            amount: int,
            is_dummy: bool = False):
        super().__init__(
            address.coin,
            address,
            index=-1,
            output_type=address.type.value.name,
            address_name=None,
            amount=amount)
        self._is_dummy: Final = is_dummy

    def __eq__(self, other: _MutableIo) -> bool:
        return (
                super().__eq__(other)
                and self._is_dummy == other._is_dummy
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._is_dummy
        ))

    @classmethod
    def deserialize(cls, *_, **__) -> Optional[_MutableIo]:
        raise DeserializationNotSupportedError

    @cached_property
    def amountBytes(self) -> bytes:
        return self._address.Script.integerToBytes(
            self._amount,
            self._AMOUNT_LENGTH,
            safe=True)

    @property
    def isDummy(self) -> bool:
        return self._is_dummy

    @cached_property
    def scriptBytes(self) -> bytes:
        raise NotImplementedError


class _MutableInput(_MutableIo):
    _HASH_TYPE_LENGTH = 0
    _SEQUENCE_LENGTH = 0

    def __init__(
            self,
            utxo: Coin.Tx.Utxo,
            *,
            hash_type: int,
            sequence: int,
            **kwargs) -> None:
        super().__init__(utxo.address, amount=utxo.amount, **kwargs)
        self._utxo: Final = utxo
        self._hash_type: Final = hash_type
        self._sequence: Final = sequence

        self._script_sig_bytes = b""
        self._witness_bytes = b""

    def __eq__(self, other: _MutableInput):
        return (
                super().__eq__(other)
                and self._utxo == other._utxo
                and self._hash_type == other._hash_type
                and self._sequence == other._sequence
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._utxo,
            self._hash_type,
            self._sequence
        ))

    @cached_property
    def scriptBytes(self) -> bytes:
        raise NotImplementedError

    @property
    def isWitness(self) -> bool:
        return self._utxo.address.type.value.isWitness

    @serializable
    @property
    def utxo(self) -> Coin.Tx.Utxo:
        return self._utxo

    @cached_property
    def utxoIdBytes(self) -> bytes:
        raise NotImplementedError

    @serializable
    @property
    def hashType(self) -> int:
        return self._hash_type

    @cached_property
    def hashTypeBytes(self) -> bytes:
        return self._address.Script.integerToBytes(
            self._hash_type,
            self._HASH_TYPE_LENGTH,
            safe=True)

    @serializable
    @property
    def sequence(self) -> int:
        return self._sequence

    @cached_property
    def sequenceBytes(self) -> bytes:
        return self._address.Script.integerToBytes(
            self._sequence,
            self._SEQUENCE_LENGTH,
            safe=True)

    @property
    def scriptSigBytes(self) -> bytes:
        return self._script_sig_bytes

    @property
    def witnessBytes(self) -> bytes:
        return self._witness_bytes

    def sign(self, hash_: bytes) -> bool:
        raise NotImplementedError


class _MutableOutput(_MutableIo):
    @cached_property
    def scriptBytes(self) -> bytes:
        raise NotImplementedError
