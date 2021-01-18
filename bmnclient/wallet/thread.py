import logging
import threading
import PySide2.QtCore as qt_core

log = logging.getLogger(__name__)


class WalletThread(qt_core.QThread):
    def __init__(self):
        super().__init__()
        self._db = None

    def run(self) -> int:
        threading.current_thread().name = "DbThread"
        from ..database import database
        self._db = database.Database()
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
