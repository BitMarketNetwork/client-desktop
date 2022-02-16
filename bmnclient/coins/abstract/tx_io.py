from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils.serialize import Serializable, serializable

if TYPE_CHECKING:
    from typing import Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedDict


class _Io(Serializable):
    def __init__(
            self,
            coin: Coin,
            *,
            row_id: int = -1,
            index: int,
            output_type: str,
            address_name: Optional[str],
            amount: int) -> None:
        super().__init__(row_id=row_id)
        self._coin = coin
        self._index = index
        self._output_type = output_type

        if not address_name:
            self._address = self._coin.Address.createNullData(
                self._coin,
                amount=amount)
        else:
            self._address = self._coin.Address.decode(
                self._coin,
                name=address_name,
                amount=amount)
            if self._address is None:
                self._address = self._coin.Address.createNullData(
                    self._coin,
                    name=address_name or "UNKNOWN",
                    amount=amount)

    def __eq__(self, other: Coin.Tx.Io) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
                and self._index == other.index
                and self._output_type == other._output_type
                and self._address == other.address
                and self._address.amount == other._address.amount
        )

    def __hash__(self) -> int:
        return hash((
            self._coin,
            self._index,
            self._output_type,
            self._address,
            self._address.amount
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
        return self._address.amount


class _MutableIo:
    _AMOUNT_LENGTH = 0

    def __init__(
            self,
            coin: Coin,
            amount: int,
            *,
            is_dummy: bool = False):
        assert amount >= 0
        self._is_dummy = is_dummy
        self._coin = coin
        self._amount = amount
        self._script_bytes = b""

    @property
    def isDummy(self) -> bool:
        return self._is_dummy

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def amountBytes(self) -> bytes:
        return self._coin.Script.integerToBytes(
            self._amount,
            self._AMOUNT_LENGTH,
            safe=True)

    @property
    def scriptBytes(self) -> bytes:
        return self._script_bytes


class _MutableInput(_MutableIo):
    _HASH_TYPE_LENGTH = 0
    _SEQUENCE_LENGTH = 0

    def __init__(
            self,
            utxo: Coin.Tx.Utxo,
            *,
            utxo_id_bytes: bytes,
            hash_type: int,
            sequence: int,
            **kwargs) -> None:
        super().__init__(utxo.coin, utxo.amount, **kwargs)
        self._utxo = utxo
        self._utxo_id_bytes = utxo_id_bytes
        self._hash_type = hash_type
        self._sequence = sequence

        self._script_sig_bytes = b""
        self._witness_bytes = b""

    def __eq__(self, other: Coin.TxFactory.MutableTx.Input):
        return (
                isinstance(other, self.__class__)
                and self._utxo_id_bytes == other._utxo_id_bytes
        )

    def __hash__(self) -> int:
        return hash((self._utxo_id_bytes, ))

    @property
    def isWitness(self) -> bool:
        return self._utxo.address.type.value.isWitness

    @property
    def utxo(self) -> Coin.Tx.Utxo:
        return self._utxo

    @property
    def utxoIdBytes(self) -> bytes:
        return self._utxo_id_bytes

    @property
    def hashType(self) -> int:
        return self._hash_type

    @property
    def hashTypeBytes(self) -> bytes:
        return self._coin.Script.integerToBytes(
            self._hash_type,
            self._HASH_TYPE_LENGTH,
            safe=True)

    @property
    def sequence(self) -> int:
        return self._sequence

    @property
    def sequenceBytes(self) -> bytes:
        return self._coin.Script.integerToBytes(
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
    def __init__(
            self,
            address: Coin.Address,
            amount: int,
            **kwargs) -> None:
        super().__init__(address.coin, amount, **kwargs)
        self._address = address
