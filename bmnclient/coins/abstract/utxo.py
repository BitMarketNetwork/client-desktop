from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from ..utils import CoinUtils
from ...utils.serialize import Serializable, serializable
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from typing import Optional
    from .coin import Coin
    from ...utils.serialize import DeserializedDict


class _Utxo(Serializable):
    def __init__(
            self,
            coin: Coin,
            *,
            name: str,
            height: int,
            index: int,
            amount: int,
            script_type: Optional[Coin.Script.Type] = None) -> None:
        super().__init__()
        self._coin = coin
        self._address: Optional[Coin.Address] = None
        self._name = name
        self._height = height
        self._index = index
        self._amount = amount
        self._script_type = script_type

    def __eq__(self, other: Coin.Tx.Utxo) -> bool:
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

    @classmethod
    def deserialize(
            cls,
            source_data: DeserializedDict,
            coin: Optional[Coin] = None,
            **options) -> Optional[Coin.Tx.Utxo]:
        assert coin is not None
        return super().deserialize(source_data, coin, **options)

    @property
    def coin(self) -> Coin:
        return self._coin

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
    def scriptType(self) -> Optional[Coin.Script.Type]:
        return self._script_type
