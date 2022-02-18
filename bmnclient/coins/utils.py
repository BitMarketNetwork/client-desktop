from __future__ import annotations

from typing import TYPE_CHECKING

from .hd import HdNode
from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from .abstract import Coin
    from ..utils.string import ClassStringKeyTuple


class CoinUtils(NotImplementedInstance):
    @classmethod
    def coinToNameKeyTuple(
            cls,
            coin: Optional[Coin]) -> Tuple[ClassStringKeyTuple, ...]:
        return (None, "no_coin" if coin is None else coin.name),

    @classmethod
    def addressToNameKeyTuple(
            cls,
            address: Optional[Coin.Address]) \
            -> Tuple[ClassStringKeyTuple, ...]:
        result = (
            *cls.coinToNameKeyTuple(None if address is None else address.coin),
            (None, "no_address" if address is None else address.name)
        )
        if isinstance(address.key, HdNode):
            result += (None, address.key.pathToString()),
        return result

    @classmethod
    def txToNameKeyTuple(
            cls,
            tx: Coin.Tx) -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.coinToNameKeyTuple(tx.coin),
            (None, tx.name)
        )

    @classmethod
    def txIoToNameKeyTuple(
            cls,
            io: Coin.Tx.Io) -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.addressToNameKeyTuple(io.address),
            (None, "io"),
            ("index", io.index),
            ("amount", io.amount)
        )

    @classmethod
    def txFactoryToNameKeyTuple(
            cls,
            factory: Coin.TxFactory) -> Tuple[ClassStringKeyTuple, ...]:
        return cls.coinToNameKeyTuple(factory.coin)

    @classmethod
    def mutableTxToNameKeyTuple(
            cls,
            mtx: Coin.TxFactory.MutableTx) \
            -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.coinToNameKeyTuple(mtx.coin),
            (None, mtx.name or "no_name")
        )

    @classmethod
    def utxoToNameKeyTuple(
            cls,
            utxo: Coin.Tx.Utxo) -> Tuple[ClassStringKeyTuple, ...]:
        return (
            *cls.addressToNameKeyTuple(utxo.address),
            (None, utxo.name),
            (None, utxo.index),
            ("amount", utxo.amount)
        )
