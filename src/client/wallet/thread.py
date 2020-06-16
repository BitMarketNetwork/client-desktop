
import logging
import sys
import PySide2.QtCore as qt_core

from .database import database

log = logging.getLogger(__name__)


class WalletThread(qt_core.QThread):

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self) -> int:
        gcd = self.parent()
        self._db = database.Database(gcd=gcd, password=gcd.passphrase)
        self.finished.connect(self._db.close,    qt_core.Qt.QueuedConnection)
        return self.exec_()

    @property
    def ready(self) -> bool:
        return hasattr(self, "_db")

    @property
    def database(self) -> database.DbWrapper:
        if not self.ready:
            log.fatal("db isn't ready")
            raise SystemExit(1)
        return self._db
