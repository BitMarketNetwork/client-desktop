import os

import PySide2.QtCore as qt_core

from .application import CoreApplication


class DebugManager(qt_core.QObject):

    def __init__(self, gcd=None):
        super().__init__(parent=gcd)

    @qt_core.Slot()
    def update(self):
        self.gcd.update_wallets()

    @qt_core.Slot()
    def poll(self):
        CoreApplication.instance().networkThread.poll_coins()

    @qt_core.Slot()
    def stopPolling(self):
        self.gcd.stop_poll()

    @qt_core.Slot()
    def reprocesstxlist(self):
        self.gcd.process_all_txs()

    @qt_core.Slot()
    def retrieveFee(self):
        CoreApplication.instance().networkThread.retrieve_fee()

    @qt_core.Slot(int)
    def kill(self, sig: int):
        os.kill(os.getpid(), sig)

    @qt_core.Slot(int, int)
    def undoTransaction(self, coin: int, count: int) -> None:
        self.gcd.undoTx.emit(self.gcd[coin], count)

    @property
    def gcd(self):
        return self.parent()
