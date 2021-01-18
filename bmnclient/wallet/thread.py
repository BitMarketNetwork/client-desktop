import logging
import threading
import PySide2.QtCore as qt_core

from ..loading_level import LoadingLevel

log = logging.getLogger(__name__)


class WalletThread(qt_core.QThread):
    applyPassword = qt_core.Signal()
    dbLoaded = qt_core.Signal(int)

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
        if level == LoadingLevel.ADDRESSES:
            from ..ui.gui import Application
            Application.instance().coinManager.update_coin_model()
