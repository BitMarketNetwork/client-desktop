from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING

from .tx_io import _Io
from .utxo import _Utxo
from ...utils.serialize import Serializable, serializable

if TYPE_CHECKING:
    from typing import Any, Iterable, List, Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedData, DeserializedDict


class _Interface:
    def __init__(
            self,
            *args,
            tx: Coin.Tx,
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tx = tx

    def afterSetHeight(self) -> None:
        raise NotImplementedError

    def afterSetTime(self) -> None:
        raise NotImplementedError


class _Tx(Serializable):
    class Status(Enum):
        PENDING = 0
        CONFIRMED = 1
        COMPLETE = 2

    Interface = _Interface
    Io = _Io
    Utxo = _Utxo

    def __init__(
            self,
            coin: Coin,
            *,
            row_id: int = -1,
            name: str,
            height: int = -1,
            time: int = -1,
            amount: int,
            fee_amount: int,
            is_coinbase: bool,
            input_list: Iterable[Coin.Tx.Io],
            output_list: Iterable[Coin.Tx.Io]) -> None:
        super().__init__(row_id=row_id)

        self._coin = coin
        self._name = name.strip().lower()

        self._height = height
        self._time = time
        self._amount = amount
        self._fee_amount = fee_amount
        self._is_coinbase = bool(is_coinbase)

        self._input_list = list(input_list)
        self._output_list = list(output_list)

        self._model: Optional[Coin.Tx.Interface] = \
            self._coin.model_factory(self)

    def __eq__(self, other: Coin.Tx) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
                and self._name == other._name
        )

    def __hash__(self) -> int:
        return hash((self._coin, self._name, ))

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            coin: Optional[Coin] = None,
            **options) -> Optional[Coin.Tx]:
        assert coin is not None
        return super().deserialize(source_data, coin, **options)

    @classmethod
    def _deserializeProperty(
            cls,
            key: str,
            value: DeserializedData,
            coin: Optional[Coin] = None,
            **options) -> Any:
        if key in ("input_list", "output_list"):
            if isinstance(value, dict):
                return cls.Io.deserialize(value, coin, **options)
            elif isinstance(value, cls.Io):
                return value
        return super()._deserializeProperty(key, value, coin, **options)

    @property
    def model(self) -> Optional[Coin.Tx.Interface]:
        return self._model

    @property
    def coin(self) -> Coin:
        return self._coin

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @property
    @lru_cache()
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
            if self._model:
                self._model.afterSetHeight()

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
            if self._model:
                self._model.afterSetTime()

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
    def inputList(self) -> List[Coin.Tx.Io]:
        return self._input_list

    @serializable
    @property
    def outputList(self) -> List[Coin.Tx.Io]:
        return self._output_list

    @staticmethod
    def toNameHuman(name: str) -> str:
        if len(name) <= 6 * 2 + 3:
            return name
        return name[:6] + "..." + name[-6:]
