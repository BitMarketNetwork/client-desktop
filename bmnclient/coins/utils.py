from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import NotImplementedInstance
from .hd import HdNode

if TYPE_CHECKING:
    from typing import Optional, Tuple

    from ..utils.string import ClassStringKeyTuple
    from .abstract import Coin

# TODO deprecated


class CoinUtils(NotImplementedInstance):
    @classmethod
    def coinToNameKeyTuple(
        cls, coin: Optional[Coin]
    ) -> Tuple[ClassStringKeyTuple, ...]:
        return ((None, "no_coin" if coin is None else coin.name),)

    @classmethod
    def addressToNameKeyTuple(
        cls, address: Optional[Coin.Address]
    ) -> Tuple[ClassStringKeyTuple, ...]:
        result = (
            *cls.coinToNameKeyTuple(None if address is None else address.coin),
            (None, "no_address" if address is None else address.name),
        )
        if isinstance(address.key, HdNode):
            result += ((None, address.key.pathToString()),)
        return result

    @classmethod
    def mutableTxToNameKeyTuple(
        cls, mtx: Coin.TxFactory.MutableTx
    ) -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.coinToNameKeyTuple(mtx.coin),
            (None, mtx.name or "no_name"),
        )
