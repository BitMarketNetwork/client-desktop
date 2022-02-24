from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from .tx_io import Io
from .utxo import Utxo
from ...utils.serialize import serializable

if TYPE_CHECKING:
    from typing import Any, Final, List, Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedData


class _Model(CoinObjectModel):
    def __init__(self, *args, tx: Tx, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tx = tx

    def afterSetHeight(self) -> None:
        raise NotImplementedError

    def afterSetTime(self) -> None:
        raise NotImplementedError


class Tx(CoinObject):
    __initialized = False

    class Status(Enum):
        PENDING = 0
        CONFIRMED = 1
        COMPLETE = 2

    Model = _Model
    Io = Io
    Utxo = Utxo

    def __new__(cls, coin: Coin, *args, **kwargs) -> Tx:
        if not kwargs.get("name"):
            return super(Tx, cls).__new__(cls)

        heap = coin.weakValueDictionary("tx_heap")
        name = kwargs["name"].lower()
        tx = heap.get(name)
        if tx is None:
            tx = super(Tx, cls).__new__(cls)
        heap[name] = tx
        return tx

    def __init__(self, coin: Coin, *, row_id: int = -1, **kwargs) -> None:
        if self.__initialized:
            assert self._coin is coin
            self.__update__(**kwargs)
            return
        self.__initialized = True

        super().__init__(coin, row_id=row_id)

        self._name: Final[str] = kwargs.get("name").lower()
        self._height: int = kwargs.get("height", -1)
        self._time: int = kwargs.get("time", -1)
        self._amount: int = kwargs["amount"]
        self._fee_amount: int = kwargs["fee_amount"]
        self._is_coinbase = bool(kwargs["is_coinbase"])

        self._input_list: Final[List[Io]] = list(kwargs["input_list"])
        self._output_list: Final[List[Io]] = list(kwargs["output_list"])

    def __eq__(self, other: Tx) -> bool:
        return (
                super().__eq__(other)
                and self._name == other._name
        )

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._name, ))

    @classmethod
    def _deserializeProperty(
            cls,
            self: Optional[Tx],
            key: str,
            value: DeserializedData,
            coin: Optional[Coin] = None,
            **options) -> Any:
        if key in ("input_list", "output_list"):
            if isinstance(value, dict):
                return cls.Io.deserialize(value, coin, **options)
            elif isinstance(value, cls.Io):
                return value
        return super()._deserializeProperty(self, key, value, coin, **options)

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
        if self._height != value:
            assert self._height == -1
            self._height = value
            self._callModel("afterSetHeight")

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
        if self._time != value:
            self._time = value
            self._callModel("afterSetTime")

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
    def inputList(self) -> List[Io]:
        return self._input_list

    @serializable
    @property
    def outputList(self) -> List[Io]:
        return self._output_list

    @staticmethod
    def toNameHuman(name: str) -> str:
        if len(name) <= 6 * 2 + 3:
            return name
        return name[:6] + "..." + name[-6:]
