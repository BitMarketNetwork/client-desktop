from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from ...utils.serialize import Serializable, serializable

if TYPE_CHECKING:
    from typing import Final, Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedDict


class _Io(Serializable):
    def __init__(
            self,
            coin: Coin,
            address: Optional[Coin.Address] = None,
            *,
            row_id: int = -1,
            index: int,
            output_type: str,
            address_name: Optional[str],
            amount: int) -> None:
        super().__init__(row_id=row_id)
        if address is not None:
            assert not address_name
            assert coin is address.coin
        elif not address_name:
            address = coin.Address.createNullData(coin)
        else:
            address = coin.Address.createFromName(coin, name=address_name)
            if address is None:
                address = coin.Address.createNullData(
                    coin,
                    name=address_name or "UNKNOWN")

        self._index: Final = index
        self._output_type: Final = output_type
        self._address: Final = address
        self._amount: Final = amount

    def __eq__(self, other: Coin.Tx.Io) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._index == other.index
                and self._output_type == other._output_type
                and self._address == other.address
                and self._amount == other._amount
        )

    def __hash__(self) -> int:
        return hash((
            self._index,
            self._output_type,
            self._address,
            self._amount
        ))

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            coin: Optional[Coin] = None,
            **options) -> Optional[Coin.Tx.Io]:
        assert coin is not None
        return super().deserialize(source_data, coin, **options)

    @serializable
    @property
    def index(self) -> index:
        return self._index

    @serializable
    @property
    def outputType(self) -> str:
        return self._output_type

    @serializable
    @property
    def addressName(self) -> Optional[str]:
        return self._address.name if not self._address.isNullData else None

    @property
    def address(self) -> Coin.Address:
        return self._address

    @serializable
    @property
    def amount(self) -> int:
        return self._amount


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
            index=-1,  # TODO
            output_type="",  # TODO
            address_name=None,
            amount=amount)
        self._is_dummy: Final = is_dummy

    def __eq__(self, other: Coin.Tx.Io) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._is_dummy == other._is_dummy
            and super().__eq__(other)
        )

    def __hash__(self) -> int:
        return hash((
            self._is_dummy,
            super().__hash__()
        ))

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            coin: Optional[Coin] = None,
            **options) -> Optional[Coin.Tx.Io]:
        return None

    @cached_property
    def amountBytes(self) -> bytes:
        return self._address.coin.Script.integerToBytes(
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

    def __eq__(self, other: Coin.TxFactory.MutableTx.Input):
        return (
                isinstance(other, self.__class__)
                and self._utxo == other._utxo
                and self._hash_type == other._hash_type
                and self._sequence == other._sequence
                and super().__eq__(other)
        )

    def __hash__(self) -> int:
        return hash((
            self._utxo,
            self._hash_type,
            self._sequence,
            super().__hash__()
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
        return self._address.coin.Script.integerToBytes(
            self._hash_type,
            self._HASH_TYPE_LENGTH,
            safe=True)

    @serializable
    @property
    def sequence(self) -> int:
        return self._sequence

    @cached_property
    def sequenceBytes(self) -> bytes:
        return self._address.coin.Script.integerToBytes(
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
