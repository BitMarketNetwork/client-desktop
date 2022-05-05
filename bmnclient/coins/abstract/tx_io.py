from __future__ import annotations

from enum import Enum
from typing import Final, TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from ...database.tables import TxIosTable
from ...utils import (
    DeserializeFlag,
    DeserializedData,
    SerializeFlag,
    serializable)
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from .coin import Coin


class _Model(CoinObjectModel):
    def __init__(self, *args, io: Coin.Tx.Io, **kwargs) -> None:
        self._io = io
        super().__init__(*args, **kwargs)

    @property
    def owner(self) -> Coin.Tx.Io:
        return self._io


class _Io(CoinObject, table_type=TxIosTable):
    Model = _Model

    class IoType(Enum):
        INPUT = "input"
        OUTPUT = "output"

    def __init__(self, tx: Coin.Tx, **kwargs) -> None:
        self._tx: Final = tx
        self._io_type: Final[_Io.IoType] = kwargs["io_type"]
        assert isinstance(self._io_type, self.IoType)
        self._index: Final = int(kwargs["index"])

        super().__init__(tx.coin, kwargs)

        self._output_type: Final = str(kwargs.pop("output_type"))
        self._address: Final[Coin.Address] = kwargs.pop("address")
        assert isinstance(self._address, self._coin.Address)
        self._amount: Final = int(kwargs.pop("amount"))
        assert len(kwargs) == 2

    def __eq__(self, other: _Io) -> bool:
        return (
                super().__eq__(other)
                and self._index == other.index
                and self._output_type == other._output_type
                and self._address == other.address
                and self._amount == other._amount)

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._index,
            self._output_type,
            self._address,
            self._amount))

    # TODO cache
    def __str__(self) -> str:
        return StringUtils.classString(
            self.__class__,
            (None, self._io_type.value),
            ("index", self._index),
            ("amount", self._amount),
            parent=self._address)

    def serializeProperty(
            self,
            flags: SerializeFlag,
            key: str,
            value: ...) -> DeserializedData:
        if key == "io_type":
            return value.value
        if key == "address":
            return value.name
        return super().serializeProperty(flags, key, value)

    @classmethod
    def deserializeProperty(
            cls,
            flags: DeserializeFlag,
            self: _Io | None,
            key: str,
            value: DeserializedData,
            *cls_args) -> ...:
        if key == "io_type":
            for io_type in cls.IoType:
                if io_type.value == value:
                    return io_type
            return None
        if key == "address":
            tx = cls_args[0] if cls_args else self._tx
            if not value:
                return tx.coin.Address.createNullData(tx.coin)
            address = tx.coin.Address.createFromName(tx.coin, name=value)
            if address is None:
                address = tx.coin.Address.createNullData(tx.coin, name=value)
            return address
        return super().deserializeProperty(flags, self, key, value, *cls_args)

    @property
    def tx(self) -> Coin.Tx:
        return self._tx

    @serializable
    @property
    def ioType(self) -> _Io.IoType:
        return self._io_type

    @serializable
    @property
    def index(self) -> int:
        return self._index

    @serializable
    @property
    def outputType(self) -> str:
        return self._output_type

    @serializable
    @property
    def address(self) -> Coin.Address:
        return self._address

    @serializable
    @property
    def amount(self) -> int:
        return self._amount
