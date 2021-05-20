# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from .abstract.coin import AbstractCoin
    from ..utils.string import ClassStringKeyTuple
    from ..wallet.mtx_impl import Mtx


class CoinUtils(NotImplementedInstance):
    @classmethod
    def coinToNameKeyTuple(
            cls,
            coin: AbstractCoin) -> Tuple[ClassStringKeyTuple, ...]:
        return (None, coin.name),

    @classmethod
    def addressToNameKeyTuple(
            cls,
            address: AbstractCoin.Address,
            hd_index: Optional[int] = None) -> Tuple[ClassStringKeyTuple, ...]:
        result = (
            *cls.coinToNameKeyTuple(address.coin),
            (None, address.name)
        )
        if hd_index is not None:
            result += ("index", hd_index),
        return result

    @classmethod
    def txToNameKeyTuple(
            cls,
            tx: AbstractCoin.Tx) -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.coinToNameKeyTuple(tx.coin),
            (None, tx.name)
        )

    @classmethod
    def mutableTxToNameKeyTuple(
            cls,
            tx: AbstractCoin.MutableTx) -> Tuple[ClassStringKeyTuple, ...]:
        return cls.coinToNameKeyTuple(tx.coin)

    @classmethod
    def mtxToNameKeyTuple(
            cls,
            tx: Mtx) -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.coinToNameKeyTuple(tx.coin),
            (None, tx.name)
        )
