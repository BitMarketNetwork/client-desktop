import logging
import PySide2.QtCore as qt_core

from ..wallet.coins import CoinType
from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class WalletThread(qt_core.QThread):
    applyPassword = qt_core.Signal()
    dbLoaded = qt_core.Signal(int)
    dropDb = qt_core.Signal()
    saveAddress = qt_core.Signal(AbstractCoin.Address, int, arguments=["wallet", "timeout"])
    saveTx = qt_core.Signal(AbstractCoin.Tx, arguments=["tx"])
    resetDb = qt_core.Signal(bytes, arguments=["password"])
    saveCoin = qt_core.Signal(CoinType, arguments=["coin"])

    def __init__(self) -> None:
        super().__init__()
        self._db = None

    def run(self) -> int:
        # threading.current_thread().name = "DbThread"
        from ..database import database
        self._db = database.Database(self)
        self.finished.connect(self._db.close, qt_core.Qt.QueuedConnection)
        # return self.exec_()
        return 0

    @property
    def database(self):
        if not hasattr(self, "_db"):
            log.fatal("db isn't ready")
            raise SystemExit(1)
        return self._db

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

    def db_level_loaded(self, level: int) -> None:
        self.dbLoaded.emit(level)

    def reset_db(self) -> None:
        self.dropDb.emit()

    def save_address(self, wallet: AbstractCoin.Address, delay_ms: int = None):
        self.saveAddress.emit(wallet, delay_ms)
