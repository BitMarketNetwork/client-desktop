# JOK4
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from ...utils.serialize import Serializable, serializable
from ...wallet.mtx_impl import UTXO

if TYPE_CHECKING:
    from typing import Any, List, Optional, Tuple
    from .address import AbstractAddress


class TxStatus(Enum):
    PENDING = 0
    CONFIRMED = 1
    COMPLETE = 2


class AbstractTxIo:
    def __init__(self, address: AbstractAddress) -> None:
        self._address = address

    @property
    def address(self) -> AbstractAddress:
        return self._address


class AbstractUtxo(Serializable):
    def __init__(
            self,
            address: AbstractAddress,
            *,
            name: str,
            height: int,
            index: int,
            amount: int) -> None:
        super().__init__()
        self._address = address
        self._name = name
        self._height = height
        self._index = index
        self._amount = amount

    @property
    def address(self) -> AbstractAddress:
        return self._address

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @serializable
    @property
    def height(self) -> int:
        return self._height

    @serializable
    @property
    def index(self) -> int:
        return self._index

    @serializable
    @property
    def amount(self) -> int:
        return self._amount


class AbstractTxInterface:
    def afterSetHeight(self) -> None:
        raise NotImplementedError

    def afterSetTime(self) -> None:
        raise NotImplementedError


class AbstractTx(Serializable):
    class TxIo(AbstractTxIo):
        pass

    class Utxo(UTXO):  # TODO AbstractUtxo
        pass

    def __init__(
            self,
            address: AbstractAddress,
            *,
            name: str,
            height: int = -1,
            time: int = -1,
            amount: int,
            fee_amount: int,
            coinbase: bool,
            input_list: List[TxIo],
            output_list: List[TxIo]) -> None:
        super().__init__()

        self._address = address
        self._name = name.strip().lower()

        self._height = height
        self._time = time
        self._amount = amount
        self._fee_amount = fee_amount
        self._coinbase = coinbase

        self._input_list = input_list
        self._output_list = output_list

        self._model: Optional[AbstractTxInterface] = \
            self._address.coin.model_factory(self)

    def __eq__(self, other: AbstractTx) -> bool:
        # TODO compare self._input_list, self._output_list
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    @classmethod
    def _deserialize(cls, args: Tuple[Any], key: str, value: Any) -> Any:
        if isinstance(value, dict):
            if key in ("input_list", "output_list"):
                return cls.TxIo(args[0].coin, **value)
        return super()._deserialize(args, key, value)

    @property
    def model(self) -> Optional[AbstractTxInterface]:
        return self._model

    @property
    def address(self) -> AbstractAddress:
        return self._address

    @serializable
    @property
    def name(self) -> str:
        return self._name

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
        if 0 <= self._height <= self._address.coin.height:
            return self._address.coin.height - self._height + 1
        return 0

    @property
    def status(self) -> TxStatus:
        c = self.confirmations
        if c <= 0:
            return TxStatus.PENDING
        if c <= 6:  # TODO const
            return TxStatus.CONFIRMED
        return TxStatus.COMPLETE

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
    def coinbase(self) -> bool:
        return self._coinbase

    @serializable
    @property
    def inputList(self) -> List[TxIo]:
        return self._input_list

    @serializable
    @property
    def outputList(self) -> List[TxIo]:
        return self._output_list

