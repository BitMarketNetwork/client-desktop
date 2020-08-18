

import logging
import os
import signal
import time

import PySide2.QtCore as qt_core

from . import constant
from .wallet import coins, mutable_tx

log = logging.getLogger(__name__)


class DebugManager(qt_core.QObject):

    def __init__(self, gcd=None):
        super().__init__(parent=gcd)

    @qt_core.Slot()
    def makeWallets(self):
        BTC_ADDRESSES = [
            "3P3QsMVK89JBNqZQv5zMAKG8FK3kJM4rjt",
            "1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX",
            "3Jb9jJVRWYVdrf3p4w1hrxdCqHkeb9FDL2",
            "bc1q3gvshn60tpsmwnrj7f4p4hc2hmsld52pazada0",  # it is mine
        ]
        LTC_ADDRESSES = [
            "LLkYZVcYDZ4h87ZcX3aHWPCzHqFgBRyRGU",
            "MTvnA4CN73ry7c65wEuTSaKzb2pNKHB4n1",
            "LWxJ1EMDaj4rC8KRyLmvgEiSCNoKjHGZXm",
        ]
        for addr in BTC_ADDRESSES:
            try:
                self.gcd.add_address(addr, coin=self.gcd.btc_coin)
            except coins.AddressError as ae:
                log.warn(ae)
        for addr in LTC_ADDRESSES:
            try:
                self.gcd.add_address(addr, coin=self.gcd.ltc_coin)
            except coins.AddressError as ae:
                log.warn(ae)

    @qt_core.Slot()
    def update(self):
        self.gcd.silent_mode = False
        self.gcd.update_wallets()

    @qt_core.Slot()
    def poll(self):
        self.gcd.silent_mode = False
        self.gcd.poll_coins()

    @qt_core.Slot()
    def stopPolling(self):
        self.gcd.silent_mode = True
        self.gcd.stop_poll()

    @qt_core.Slot()
    def reprocesstxlist(self):
        self.gcd.process_all_txs()

    @qt_core.Slot()
    def retrieveFee(self):
        self.gcd.retrieve_fee()

    @qt_core.Slot()
    def simulateTxBroadcasting(self):
        address = self.gcd.first_test_address
        self.gcd.unspent_list(address)
        counter = 0
        while not address.unspents:
            # 2 secs
            if counter > 20:
                raise RuntimeError(f"No unspents for {address}")
            time.sleep(0.1)
            counter += 1
            log.warning(f"Wait for UTXO: {counter}")
        mtx = mutable_tx.MutableTransaction.make_dummy(
            address, self)
        self.gcd.broadcastMtx.emit(mtx)

    @qt_core.Slot()
    def reload(self):
        log.info("reloading QML")
        self.gcd.reloadQml.emit()

    @qt_core.Slot()
    def restart(self):
        log.info("restarting app")
        # TODO

    @qt_core.Slot(int)
    def kill(self, sig: int):
        os.kill(os.getpid(), sig)

    @qt_core.Slot(int, int)
    def undoTransaction(self, coin: int, count: int) -> None:
        self.gcd.undoTx.emit(self.gcd[coin], count)

    @qt_core.Slot(int)
    def simulateHTTPError(self, code: int) -> None:
        self.gcd.httpFailureSimulation.emit(code)

    @qt_core.Slot(str)
    def simulateClientVersion(self, client_version: str):
        self.gcd.set_settings(constant.CLIENT_VERSION, client_version)
        qt_core.QCoreApplication.quit()

    @property
    def gcd(self):
        return self.parent()
