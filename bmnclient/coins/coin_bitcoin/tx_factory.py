# JOK4
from __future__ import annotations

from ..abstract.coin import AbstractCoin


class _BitcoinMutableTx(AbstractCoin.TxFactory.MutableTx):
    pass


class _BitcoinTxFactory(AbstractCoin.TxFactory):
    MutableTx = _BitcoinMutableTx










