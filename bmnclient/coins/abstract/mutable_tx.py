from __future__ import annotations

from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, Final, Iterable, TypeVar

from ...utils import SerializableList, serializable
from .tx import _Tx

if TYPE_CHECKING:
    from .coin import Coin


class _MutableTx(_Tx, table_type=None):
    _VERSION_LENGTH = 0
    _LOCK_TIME_LENGTH = 0

    from .mutable_tx_io import _MutableInput, _MutableOutput

    Input = _MutableInput
    Output = _MutableOutput

    _ioT = TypeVar("_ioT", Input, Output)

    class IoList(SerializableList[_ioT]):
        def __init__(
            self, tx: _MutableTx, type_: type(_MutableTx._ioT)
        ) -> None:
            self._tx = tx
            self._type = type_
            self._list: list[_MutableTx._ioT] = []

        def __len__(self) -> int:
            return len(self._list)

        def __iter__(self) -> Iterable[_MutableTx._ioT]:
            return iter(self._list)

        def __getitem__(self, index: int) -> Coin.Address:
            return self._list[index]

        def __setitem__(self, index: int, io: _MutableTx._ioT) -> None:
            raise NotImplementedError

        def __delitem__(self, index: int) -> None:
            raise NotImplementedError

        def insert(self, index: int, value: dict[str, ...]) -> bool:
            raise NotImplementedError

        def append(self, value: dict[str, ...]) -> _MutableTx._ioT:
            io = self._type(self._tx, index=len(self._list), **value)
            self._list.append(io)
            self._tx._updateAmount()
            return io

        def clear(self) -> None:
            self._list.clear()
            self._tx._updateAmount()

    def __init__(
        self,
        coin: Coin,
        *,
        time: int = -1,
        version: int,
        lock_time: int,
        is_dummy: bool = False,
    ):
        super().__init__(
            coin, name="", time=time, amount=0, fee_amount=0, is_coinbase=False
        )
        self._is_dummy: Final = is_dummy
        self._version: Final = version
        self._lock_time: Final = lock_time
        self._is_signed = False

        self._input_list = self.IoList(self, self.Input)
        self._output_list = self.IoList(self, self.Output)

    def __eq__(self, other: _MutableTx) -> bool:
        return (
            super().__eq__(other)
            and self._is_dummy == other._is_dummy
            and self._version == other._version
            and self._lock_time == other._lock_time
            and self._input_list == other._input_list
            and self._output_list == other._output_list
        )

    def __hash__(self) -> int:
        return hash(
            (
                super().__hash__(),
                self._is_dummy,
                self._version,
                self._lock_time,
                *(io.__hash__() for io in self._input_list),
                *(io.__hash__() for io in self._output_list),
            )
        )

    @cached_property
    def name(self) -> str | None:
        if not self._is_signed or self._is_dummy:
            return None
        return self._deriveName()

    @serializable
    @property
    def inputList(self) -> IoList[Input]:
        return self._input_list

    @serializable
    @property
    def outputList(self) -> IoList[Output]:
        return self._output_list

    @property
    def isDummy(self) -> bool:
        return self._is_dummy

    @property
    def version(self) -> int:
        return self._version

    @property
    def versionBytes(self) -> bytes:
        return self._coin.Address.Script.integerToBytes(
            self._version, self._VERSION_LENGTH, safe=True
        )

    @property
    def lockTime(self) -> int:
        return self._lock_time

    @property
    def lockTimeBytes(self) -> bytes:
        return self._coin.Address.Script.integerToBytes(
            self._lock_time, self._LOCK_TIME_LENGTH, safe=True
        )

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

    def _deriveName(self) -> str | None:
        raise NotImplementedError

    def _updateAmount(self) -> None:
        self._amount = sum(i.amount for i in self._input_list)
        output_amount = sum(o.amount for o in self._output_list)
        self._fee_amount = self._amount - output_amount
