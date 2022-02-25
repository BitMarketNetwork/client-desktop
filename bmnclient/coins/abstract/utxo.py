from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .object import CoinObject
from ..utils import CoinUtils
from ...utils.serialize import serializable
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from typing import Final, Optional
    from .coin import Coin


class _Utxo(CoinObject):
    def __init__(
            self,
            coin: Coin,
            *,
            name: str,
            height: int,
            index: int,
            amount: int,
            script_type: Optional[Coin.Address.Script.Type] = None) -> None:
        super().__init__(coin)
        self._address: Optional[Coin.Address] = None
        self._name: Final = name
        self._height: Final = height
        self._index: Final = index
        self._amount: Final = amount
        self._script_type = script_type

    def __eq__(self, other: _Utxo) -> bool:
        return (
                super().__eq__(other)
                and self._name == other._name
                and self._height == other._height
                and self._index == other._index
                and self._amount == other._amount
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
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
    def address(self) -> Optional[Coin.Address]:
        return self._address

    @address.setter
    def address(self, address: Coin.Address) -> None:
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

    @cached_property
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
    def scriptType(self) -> Optional[Coin.Address.Script.Type]:
        return self._script_type
