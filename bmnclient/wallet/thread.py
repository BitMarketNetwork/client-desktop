import logging
import threading
import PySide2.QtCore as qt_core

from ..loading_level import LoadingLevel
from ..wallet.coins import CoinType
from .address import CAddress
from ..wallet import tx
log = logging.getLogger(__name__)


class WalletThread(qt_core.QThread):
    applyPassword = qt_core.Signal()
    dbLoaded = qt_core.Signal(int)
    saveTxList = qt_core.Signal(CAddress, list)
    dropDb = qt_core.Signal()
    clearAddressTx = qt_core.Signal(CAddress, arguments=["address"])
    saveAddress = qt_core.Signal(CAddress, int, arguments=["wallet", "timeout"])
    eraseWallet = qt_core.Signal(CAddress, arguments=["wallet"])
    saveTx = qt_core.Signal(tx.Transaction, arguments=["tx"])
    resetDb = qt_core.Signal(bytes, arguments=["password"])
    removeTxList = qt_core.Signal(list)
    saveCoin = qt_core.Signal(CoinType, arguments=["coin"])

    def __init__(self):
        super().__init__()
        self._db = None

    def run(self) -> int:
        threading.current_thread().name = "DbThread"
        from ..database import database
        self._db = database.Database(self)
        self.finished.connect(self._db.close, qt_core.Qt.QueuedConnection)
        return self.exec_()

    @property
    def database(self):
        if not hasattr(self, "_db"):
            log.fatal("db isn't ready")
            raise SystemExit(1)
        return self._db

    def save_coins_with_addresses(self):
        qt_core.QMetaObject.invokeMethod(
            self._db,
            "save_coins_with_addresses",
            qt_core.Qt.QueuedConnection)

    def save_coins_settings(self):  # TODO call from SettingsManager
        qt_core.QMetaObject.invokeMethod(
            self._db,
            "save_coins_settings",
            qt_core.Qt.QueuedConnection)

    def db_level_loaded(self, level: int) -> None:
        self.dbLoaded.emit(level)

    def save_tx_list(self, address, tx_list):
        self.saveTxList.emit(address, tx_list)

    def reset_db(self) -> None:
        self.dropDb.emit()

    def clear_transactions(self, address):
        self.clearAddressTx.emit(address)
        address.clear()
        # to save offsetts
        self.saveAddress.emit(address, None)

    def save_wallet(self, wallet: CAddress, delay_ms: int = None):
        self.saveAddress.emit(wallet, delay_ms)

    def delete_wallet(self, wallet):
        self.eraseWallet.emit(wallet)
        wallet.coin.remove_wallet(wallet)
