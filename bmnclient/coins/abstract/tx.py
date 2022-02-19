from __future__ import annotations

from enum import Enum
from functools import cached_property, lru_cache
from typing import TYPE_CHECKING

from .serialize import _CoinSerializable
from .tx_io import _Io, _MutableInput, _MutableOutput
from .utxo import _Utxo
from ...debug import Debug
from ...utils.serialize import serializable

if TYPE_CHECKING:
    from typing import Any, Final, Iterable, List, Optional, Sequence
    from .coin import Coin
    from ...utils.serialize import DeserializedData


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


class _Tx(_CoinSerializable):
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
        #Debug.assertObjectCaller(coin, "_allocateTx")
        super().__init__(row_id=row_id)

        self._coin: Final = coin
        self._name: Final = name.strip().lower()

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

    @classmethod
    def _deserializeFactory(
            cls,
            coin: Coin,
            **kwargs) -> Optional[Coin.Address]:
        # noinspection PyProtectedMember
        return coin._allocateTx(**kwargs)

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


class _MutableTx(_Tx):
    _VERSION_LENGTH = 0
    _LOCK_TIME_LENGTH = 0

    Input = _MutableInput
    Output = _MutableOutput

    def __init__(
            self,
            coin: Coin,
            input_list: Sequence[Input],
            output_list: Sequence[Output],
            *,
            version: int,
            lock_time: int,
            is_dummy: bool = False,
            time: int = -1,
            amount: int,
            fee_amount: int):
        # TODO move after super().__init__()
        self._is_dummy = is_dummy
        self._version = version
        self._lock_time = lock_time
        self._is_witness = any(i.isWitness for i in input_list)
        self._is_signed = False
        super().__init__(
            coin,
            name="mutable_tx", # TODO
            height=-1,
            time=time,
            amount=amount,
            fee_amount=fee_amount,
            is_coinbase=False,
            input_list=input_list,
            output_list=output_list)

    @property
    def isDummy(self) -> bool:
        return self._is_dummy

    def _deriveName(self) -> Optional[str]:
        raise NotImplementedError

    @cached_property
    def name(self) -> Optional[str]:
        if not self._is_signed or self._is_dummy:
            return None
        return self._deriveName()

    @property
    def coin(self) -> Coin:
        return self._coin

    @property
    def version(self) -> int:
        return self._version

    @property
    def versionBytes(self) -> bytes:
        return self._coin.Script.integerToBytes(
            self._version,
            self._VERSION_LENGTH,
            safe=True)

    @property
    def lockTime(self) -> int:
        return self._lock_time

    @property
    def lockTimeBytes(self) -> bytes:
        return self._coin.Script.integerToBytes(
            self._lock_time,
            self._LOCK_TIME_LENGTH,
            safe=True)

    @property
    def isWitness(self) -> bool:
        return self._is_witness

    @property
    def isSigned(self) -> bool:
        return self._is_signed

    def _sign(self) -> bool:
        raise NotImplementedError

    def sign(self) -> bool:
        self.__class__.serialize.cache_clear()
        # noinspection PyUnresolvedReferences
        self.__dict__.pop(self.__class__.name.attrname, None)

        if not self._is_signed and self._sign():
            self._is_signed = True
            return True
        return False

    def _serialize(self, *, with_witness: bool = True, **kwargs) -> bytes:
        raise NotImplementedError

    @lru_cache()
    def serialize(self, *, with_witness: bool = True, **kwargs) -> bytes:
        if not self._is_signed:
            return b""
        return self._serialize(with_witness=with_witness, **kwargs)

    @property
    def rawSize(self) -> int:
        return len(self.serialize(with_witness=True))

    @property
    def virtualSize(self) -> int:
        raise NotImplementedError
