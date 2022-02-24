from __future__ import annotations

from enum import Enum
from functools import cached_property, lru_cache
from typing import TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from .tx_io import Io, MutableInput, MutableOutput
from .utxo import Utxo
from ...utils.serialize import serializable

if TYPE_CHECKING:
    from typing import Any, Final, List, Optional, Sequence
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


class MutableTx(Tx):
    _VERSION_LENGTH = 0
    _LOCK_TIME_LENGTH = 0

    Input = MutableInput
    Output = MutableOutput

    def __init__(
            self,
            coin: Coin,
            input_list: Sequence[Input],
            output_list: Sequence[Output],
            *,
            version: int,
            lock_time: int,
            is_dummy: bool = False):
        amount = sum(i.amount for i in input_list)
        fee_amount = amount - sum(o.amount for o in output_list)
        super().__init__(
            coin,
            name="",
            height=-1,
            time=-1,
            amount=amount,
            fee_amount=fee_amount,
            is_coinbase=False,
            input_list=input_list,
            output_list=output_list)
        self._is_dummy: Final = is_dummy
        self._version: Final = version
        self._lock_time: Final = lock_time
        self._is_signed = False

    def __eq__(self, other: MutableTx) -> bool:
        return (
                super().__eq__(other)
                and self._is_dummy == other._is_dummy
                and self._version == other._version
                and self._lock_time == other._lock_time
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._is_dummy,
            self._version,
            self._lock_time
        ))

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

    @cached_property
    def isWitness(self) -> bool:
        # noinspection PyUnresolvedReferences
        return any(i.isWitness for i in self._input_list)

    @property
    def isSigned(self) -> bool:
        return self._is_signed

    def _sign(self) -> bool:
        raise NotImplementedError

    def sign(self) -> bool:
        self.__class__.raw.cache_clear()
        # noinspection PyUnresolvedReferences
        self.__dict__.pop(self.__class__.name.attrname, None)

        if not self._is_signed and self._sign():
            self._is_signed = True
            return True
        return False

    def _raw(self, *, with_witness: bool = True, **kwargs) -> bytes:
        raise NotImplementedError

    @lru_cache()
    def raw(self, *, with_witness: bool = True, **kwargs) -> bytes:
        if not self._is_signed:
            return b""
        return self._raw(with_witness=with_witness, **kwargs)

    @property
    def rawSize(self) -> int:
        return len(self.raw(with_witness=True))

    @property
    def virtualSize(self) -> int:
        raise NotImplementedError
