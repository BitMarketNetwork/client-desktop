# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from .abstract.coin import AbstractCoin
    from ..utils.string import ClassStringKeyTuple


class CoinUtils(NotImplementedInstance):
    @classmethod
    def coinToNameKeyTuple(
            cls,
            coin: AbstractCoin) -> Tuple[ClassStringKeyTuple]:
        return (None, coin.name),

    @classmethod
    def addressToNameKeyTuple(
            cls,
            address: AbstractCoin.Address,
            hd_index: Optional[int] = None) -> Tuple[ClassStringKeyTuple]:
        result = cls.coinToNameKeyTuple(address.coin)
        result += (None, address.name),
        if hd_index is not None:
            result += ("index", hd_index),
        return result

    @classmethod
    def txToNameKeyTuple(
            cls,
            tx: AbstractCoin.Tx) -> Tuple[ClassStringKeyTuple]:
        result = cls.coinToNameKeyTuple(tx.coin)
        result += (None, tx.name),
        return result
