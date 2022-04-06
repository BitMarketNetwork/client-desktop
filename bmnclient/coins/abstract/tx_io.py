from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from ..utils import CoinUtils
from ...database.tables import TxIosTable
from ...utils import serializable

if TYPE_CHECKING:
    from typing import Any, Final, Optional
    from .coin import Coin
    from ...utils import DeserializeFlag, DeserializedData, SerializeFlag


class _Model(CoinObjectModel):
    def __init__(self, *args, io: Coin.Tx.Io, **kwargs) -> None:
        super().__init__(
            *args,
            name_key_tuple=CoinUtils.txIoToNameKeyTuple(io),
            **kwargs)
        self._io = io

    @property
    def owner(self) -> Coin.Tx.Io:
        return self._io


class _Io(CoinObject, table_type=TxIosTable):
    Model = _Model

    class IoType(Enum):
        INPUT: Final = "input"
        OUTPUT: Final = "output"

    def __init__(self, tx: Coin.Tx, **kwargs) -> None:
        self._tx: Final = tx
        self._io_type: Final[_Io.IoType] = kwargs["io_type"]
        if not isinstance(self._io_type, self.IoType):
            raise TypeError("invalid 'io_type' value")
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
                and self._amount == other._amount
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._index,
            self._output_type,
            self._address,
            self._amount
        ))

    def serializeProperty(
            self,
            flags: SerializeFlag,
            key: str,
            value: Any) -> DeserializedData:
        if key == "io_type":
            return value.value
        if key == "address":
            return value.name
        return super().serializeProperty(flags, key, value)

    @classmethod
    def deserializeProperty(
            cls,
            flags: DeserializeFlag,
            self: Optional[_Io],
            key: str,
            value: DeserializedData,
            *cls_args) -> Any:
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
