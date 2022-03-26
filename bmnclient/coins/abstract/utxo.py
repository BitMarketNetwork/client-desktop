from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from ..utils import CoinUtils
from ...database.tables import UtxoListTable
from ...utils import serializable
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from typing import Final
    from .coin import Coin


class _Model(CoinObjectModel):
    def __init__(self, *args, utxo: Coin.Tx.Utxo, **kwargs) -> None:
        super().__init__(
            *args,
            name_key_tuple=CoinUtils.utxoToNameKeyTuple(utxo),
            **kwargs)
        self._utxo = utxo

    @property
    def owner(self) -> Coin.Tx.Utxo:
        return self._utxo


class _Utxo(CoinObject, table_type=UtxoListTable):
    Model = _Model

    def __init__(self, address: Coin.Address,  **kwargs) -> None:
        self._address: Final = address
        self._name: Final = str(kwargs["name"])

        super().__init__(address.coin, kwargs)

        self._index: Final = int(kwargs.pop("index"))
        self._height: Final = int(kwargs.pop("height"))
        self._amount: Final = int(kwargs.pop("amount"))
        assert len(kwargs) == 1

    def __eq__(self, other: _Utxo) -> bool:
        return (
                super().__eq__(other)
                and self._name == other._name
                and self._index == other._index
                and self._height == other._height
                and self._amount == other._amount
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._name,
            self._index,
            self._height,
            self._amount
        ))

    def __str__(self) -> str:
        return StringUtils.classString(
            self.__class__,
            *CoinUtils.utxoToNameKeyTuple(self))

    @property
    def address(self) -> Coin.Address:
        return self._address

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
    def scriptType(self) -> Coin.Address.Script.Type:
        return self._address.type.value.scriptType
