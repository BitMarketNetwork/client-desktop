import logging
from typing import Optional
import PySide2.QtCore as qt_core

from . import address
from .. import meta

log = logging.getLogger(__name__)


class RootAddress(address.CAddress):
    is_root = True
    balanceChanged = qt_core.Signal()
    txCountChanged = qt_core.Signal()

    def __init__(self, coin: 'coins.CoinType'):
        super().__init__("  ", coin=coin)

    @qt_core.Property("qint64", notify=balanceChanged)
    def balance(self) -> int:
        return self._coin.balance

    @qt_core.Property(int, notify=txCountChanged)
    def realTxCount(self) -> int:
        return self._coin.tx_count

    @qt_core.Property(int, notify=txCountChanged)
    def safeTxCount(self) -> int:
        # TODO: i dont know server tx_count for coin so far
        return self._coin.tx_count

    @qt_core.Property(str, notify=balanceChanged)
    def fiatBalance(self) -> str:
        return self._coin.fiatBalance

    @qt_core.Property(bool, constant=True)
    def canSend(self) -> bool:
        return True

    @qt_core.Property(bool, constant=True)
    def readOnly(self) -> bool:
        return True

    def __call__(self, idx: int = 0) -> Optional[address.CAddress]:
        """
        returns child address
        """
        if idx < len(self._coin):
            return self._coin[idx]

    def __len__(self):
        return self._coin.tx_count

    def __getitem__(self, val: int) -> 'tx.Transaction':
        return self._coin.get_tx(val)

    def __str__(self) -> str:
        return f"root address for {self._coin.name}"

    def __contains__(self, w: address.CAddress) -> bool:
        return w in self._coin
