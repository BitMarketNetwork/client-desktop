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
            coin: Optional[AbstractCoin]) -> Tuple[ClassStringKeyTuple, ...]:
        return (None, "no_coin" if coin is None else coin.name),

    @classmethod
    def addressToNameKeyTuple(
            cls,
            address: Optional[AbstractCoin.Address],
            hd_index: Optional[int] = None) -> Tuple[ClassStringKeyTuple, ...]:
        result = (
            *cls.coinToNameKeyTuple(None if address is None else address.coin),
            (None, "no_address" if address is None else address.name)
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
    def txFactoryToNameKeyTuple(
            cls,
            factory: AbstractCoin.TxFactory) -> Tuple[ClassStringKeyTuple, ...]:
        return cls.coinToNameKeyTuple(factory.coin)

    @classmethod
    def mutableTxToNameKeyTuple(
            cls,
            mtx: AbstractCoin.TxFactory.MutableTx) \
            -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.coinToNameKeyTuple(mtx.coin),
            (None, mtx.name or "no_name")
        )

    @classmethod
    def utxoToNameKeyTuple(
            cls,
            utxo: AbstractCoin.Tx.Utxo) -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.addressToNameKeyTuple(utxo.address),
            (None, utxo.name),
            (None, utxo.index),
            ("amount", utxo.amount)
        )
