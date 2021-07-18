from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING

from ..utils import CoinUtils
from ...utils import Utils
from ...utils.serialize import Serializable, serializable
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from typing import Any, List, Optional, Tuple
    from .coin import AbstractCoin
    from ...utils.serialize import DeserializedData


class _AbstractTxIo(Serializable):
    def __init__(
            self,
            coin: AbstractCoin,
            *,
            output_type: str,
            address_name: Optional[str],
            amount: int) -> None:
        super().__init__()
        self._coin = coin
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

    def __eq__(self, other: AbstractCoin.Tx.Io) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
                and self._address == other.address
                and self._address.amount == other._address.amount
                and self._output_type == other._output_type
        )

    def __hash__(self) -> int:
        return hash((
            self._coin,
            self._address,
            self._address.amount,
            self._output_type
        ))

    def serialize(self, **options) -> DeserializedData:
        if self._address.isNullData:
            address_name = None
        else:
            address_name = self._address.name

        return {
            "output_type": self._output_type,
            "address_name": address_name,
            "amount": self._address.amount,
            **super().serialize(**options)
        }

    @property
    def outputType(self) -> str:
        return self._output_type

    @property
    def address(self) -> AbstractCoin.Address:
        return self._address


class _AbstractUtxo(Serializable):
    def __init__(
            self,
            coin: AbstractCoin,
            *,
            name: str,
            height: int,
            index: int,
            amount: int,
            script_type: Optional[AbstractCoin.Script.Type] = None) -> None:
        super().__init__()
        self._coin = coin
        self._address: Optional[AbstractCoin.Address] = None
        self._name = name
        self._height = height
        self._index = index
        self._amount = amount
        self._script_type = script_type

    def __eq__(self, other: AbstractCoin.Tx.Utxo) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
                and self._name == other._name
                and self._height == other._height
                and self._index == other._index
                and self._amount == other._amount
        )

    def __hash__(self) -> int:
        return hash((
            self._coin,
            self._name,
            self._height,
            self._index,
            self._amount
        ))

    def __str__(self) -> str:
        return StringUtils.classString(
            self.__class__,
            *CoinUtils.utxoToNameKeyTuple(self))

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @property
    def address(self) -> Optional[AbstractCoin.Address]:
        return self._address

    @address.setter
    def address(self, address: AbstractCoin.Address) -> None:
        if self._address is not None:
            raise AttributeError(
                "already associated with address '{}'"
                .format(self._address.name))
        self._address = address
        if self._script_type is None:
            self._script_type = self._address.type.value.scriptType

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @property
    @lru_cache()
    def nameHuman(self) -> str:
        return self._coin.Tx.toNameHuman(self._name)

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

    @property
    def scriptType(self) -> Optional[AbstractCoin.Script.Type]:
        return self._script_type


class _AbstractTxInterface:
    def __init__(
            self,
            *args,
            tx: AbstractCoin.Tx,
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tx = tx

    def afterSetHeight(self) -> None:
        raise NotImplementedError

    def afterSetTime(self) -> None:
        raise NotImplementedError


class _AbstractTx(Serializable):
    class Status(Enum):
        PENDING = 0
        CONFIRMED = 1
        COMPLETE = 2

    Interface = _AbstractTxInterface
    Io = _AbstractTxIo
    Utxo = _AbstractUtxo

    def __init__(
            self,
            coin: AbstractCoin,
            *,
            name: str,
            height: int = -1,
            time: int = -1,
            amount: int,
            fee_amount: int,
            coinbase: bool,
            input_list: List[AbstractCoin.Tx.Io],
            output_list: List[AbstractCoin.Tx.Io]) -> None:
        super().__init__()

        self._coin = coin
        self._name = name.strip().lower()

        self._height = height
        self._time = time
        self._amount = amount
        self._fee_amount = fee_amount
        self._coinbase = coinbase

        self._input_list = list(Utils.filterNotNone(input_list))
        self._output_list = list(Utils.filterNotNone(output_list))

        self._model: Optional[AbstractCoin.Tx.Interface] = \
            self._coin.model_factory(self)

    def __eq__(self, other: AbstractCoin.Tx) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other._coin
                and self._name == other._name
        )

    def __hash__(self) -> int:
        return hash((self._coin, self._name, ))

    @classmethod
    def _deserializeProperty(
            cls,
            args: Tuple[Any],
            key: str,
            value: Any) -> Any:
        if isinstance(value, dict) and key in ("input_list", "output_list"):
            coin: AbstractCoin = args[0]
            return cls.Io.deserialize(coin, **value)
        return super()._deserializeProperty(args, key, value)

    @property
    def model(self) -> Optional[AbstractCoin.Tx.Interface]:
        return self._model

    @property
    def coin(self) -> AbstractCoin:
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
    def coinbase(self) -> bool:
        return self._coinbase

    @serializable
    @property
    def inputList(self) -> List[AbstractCoin.Tx.Io]:
        return self._input_list

    @serializable
    @property
    def outputList(self) -> List[AbstractCoin.Tx.Io]:
        return self._output_list

    @staticmethod
    def toNameHuman(name: str) -> str:
        if len(name) <= 6 * 2 + 3:
            return name
        return name[:6] + "..." + name[-6:]
