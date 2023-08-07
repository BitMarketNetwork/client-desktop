from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Final

from ...database.tables import TxIosTable, TxsTable
from ...utils import (
    DeserializedData,
    DeserializeFlag,
    SerializableList,
    serializable,
)
from ...utils.string import StringUtils
from .object import CoinObject, CoinObjectModel

if TYPE_CHECKING:
    from .coin import Coin


class _Model(CoinObjectModel):
    def __init__(self, *args, tx: Coin.Tx, **kwargs) -> None:
        self._tx = tx
        super().__init__(*args, **kwargs)

    @property
    def owner(self) -> Coin.Tx:
        return self._tx

    def beforeSetHeight(self, value: int) -> None:
        pass

    def afterSetHeight(self, value: int) -> None:
        pass

    def beforeSetTime(self, value: int) -> None:
        pass

    def afterSetTime(self, value: int) -> None:
        pass


class _Tx(CoinObject, table_type=TxsTable):
    __initialized = False

    class Status(Enum):
        PENDING = 0
        CONFIRMED = 1
        COMPLETE = 2

    Model = _Model

    from .tx_io import _Io

    Io = _Io

    from .utxo import _Utxo

    Utxo = _Utxo

    def __new__(cls, coin: Coin, *args, **kwargs) -> _Tx:
        if not kwargs.get("name"):
            return super().__new__(cls)

        heap = coin.weakValueDictionary("tx_heap")
        name = kwargs["name"].lower()
        tx = heap.get(name)
        if tx is None:
            tx = super().__new__(cls)
        heap[name] = tx
        return tx

    def __init__(self, coin: Coin, **kwargs) -> None:
        if self.__initialized:
            assert self._coin is coin
            self.__update__(**kwargs)
            return
        self.__initialized = True
        self._name: Final = str(kwargs.get("name")).lower()

        super().__init__(coin, kwargs)

        self._height = int(kwargs.pop("height", -1))
        self._time = int(kwargs.pop("time", -1))
        self._amount = int(kwargs.pop("amount"))
        self._fee_amount = int(kwargs.pop("fee_amount"))
        self._is_coinbase: Final = bool(kwargs.pop("is_coinbase"))
        self._appendDeferredSave(
            lambda: self.inputList, kwargs.pop("input_list", [])
        )
        self._appendDeferredSave(
            lambda: self.outputList, kwargs.pop("output_list", [])
        )
        assert len(kwargs) == 1

    def __eq__(self, other: _Tx) -> bool:
        return super().__eq__(other) and self._name == other._name

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._name))

    # TODO cache
    def __str__(self) -> str:
        return StringUtils.classString(
            self.__class__, (None, self._name), parent=self.coin
        )

    def __update__(self, **kwargs) -> bool:
        self._appendDeferredSave(
            lambda: self.inputList, kwargs.pop("input_list", [])
        )
        self._appendDeferredSave(
            lambda: self.outputList, kwargs.pop("output_list", [])
        )
        if not super().__update__(**kwargs):
            return False
        # TODO self.updateBalance()
        return True

    @classmethod
    def deserializeProperty(
        cls,
        flags: DeserializeFlag,
        self: _Tx | None,
        key: str,
        value: DeserializedData,
        *cls_args,
    ) -> ...:
        if key in ("input_list", "output_list") and isinstance(value, dict):
            return lambda tx: cls.Io.deserialize(flags, value, tx)
        return super().deserializeProperty(flags, self, key, value, *cls_args)

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @cached_property
    def nameHuman(self) -> str:
        return self.toNameHuman(self._name)

    @serializable
    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._updateValue("set", "height", value)

    @property
    def confirmations(self) -> int:
        if 0 <= self._height <= self._coin.height:
            return self._coin.height - self._height + 1
        return 0

    @property
    def status(self) -> Status:
        c = self.confirmations
        if c <= 0:
            return self.Status.PENDING
        if c <= 6:  # TODO const
            return self.Status.CONFIRMED
        return self.Status.COMPLETE

    @serializable
    @property
    def time(self) -> int:
        return self._time

    @time.setter
    def time(self, value: int) -> None:
        self._updateValue("set", "time", value)

    @serializable
    @property
    def amount(self) -> int:
        return self._amount

    @serializable
    @property
    def feeAmount(self) -> int:
        return self._fee_amount

    @serializable
    @property
    def isCoinbase(self) -> bool:
        return self._is_coinbase

    @serializable
    @property
    def inputList(self) -> SerializableList[_Tx.Io]:
        return self._rowList(TxIosTable, self.Io.IoType.INPUT)

    @serializable
    @property
    def outputList(self) -> SerializableList[_Tx.Io]:
        return self._rowList(TxIosTable, self.Io.IoType.OUTPUT)

    @staticmethod
    def toNameHuman(name: str) -> str:
        if len(name) <= 6 * 2 + 3:
            return name
        return name[:6] + "..." + name[-6:]
