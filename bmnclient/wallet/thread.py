import logging
import PySide2.QtCore as qt_core

from ..wallet.coins import CoinType
from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class WalletThread(qt_core.QThread):
    saveAddress = qt_core.Signal(AbstractCoin.Address, int, arguments=["wallet", "timeout"])
    saveTx = qt_core.Signal(AbstractCoin.Tx, arguments=["tx"])
    resetDb = qt_core.Signal(bytes, arguments=["password"])
    saveCoin = qt_core.Signal(CoinType, arguments=["coin"])

    def save_coins_with_addresses(self) -> None:
               qt_core.QMetaObject.invokeMethod( # noqa
            self._db,
            "save_coins_with_addresses",
            qt_core.Qt.QueuedConnection)

    def save_coins_settings(self) -> None:  # TODO call from SettingsManager
        qt_core.QMetaObject.invokeMethod( # noqa
            self._db,
            "save_coins_settings",
            qt_core.Qt.QueuedConnection)

    def save_address(self, wallet: AbstractCoin.Address, delay_ms: int = None):
        self.saveAddress.emit(wallet, delay_ms)
