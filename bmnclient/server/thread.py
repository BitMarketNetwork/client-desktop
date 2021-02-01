import threading
import PySide2.QtCore as qt_core
from ..wallet.coins import CoinType
from ..wallet.address import CAddress
from ..wallet import mutable_tx, tx


class ServerThread(qt_core.QThread):
    mempoolEveryCoin = qt_core.Signal()
    mempoolCoin = qt_core.Signal(CoinType, arguments=["coin"])
    lookForHDChain = qt_core.Signal(CoinType, arguments=["coin"])
    unspentsOfWallet = qt_core.Signal(CAddress, arguments=["wallet"])
    updateAddress = qt_core.Signal(CAddress, arguments=["wallet"])
    undoTx = qt_core.Signal(CoinType, int)
    retrieveCoinHistory = qt_core.Signal(CoinType, arguments=["coin"])
    broadcastMtx = qt_core.Signal(mutable_tx.MutableTransaction, arguments=["mtx"])
    netError = qt_core.Signal(int, str, arguments=["code,error"])
    updateTxStatus = qt_core.Signal(tx.Transaction)
    heightChanged = qt_core.Signal(CoinType, arguments=["coin"])

    def __init__(self):
        super().__init__()
        self.finished.connect(self.deleteLater)
        self._network = None
        self._poll_timer = None
        self._mempool_timer = None

    def run(self):
        threading.current_thread().name = "ServerThread"
        from .network import Network
        self._poll_timer = qt_core.QBasicTimer()
        self._mempool_timer = qt_core.QBasicTimer()
        self._network = Network(self)
        self.setPriority(qt_core.QThread.LowPriority)
        # self.finished.connect(self.??.close,    qt_core.Qt.QueuedConnection)
        self.exec_()
        self._mempool_timer.stop()
        self._poll_timer.stop()

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._poll_timer.timerId():
            self.poll_coins()
            if self._poll_timer.short:
                #log.debug("increase polling timeout")
                self._poll_timer.short = False
                self._poll_timer.start(30 * 1000, self)
        elif event.timerId() == self._mempool_timer.timerId():
            self.mempoolEveryCoin.emit()

    def startTimers(self):
        self._poll_timer.short = True
        self._poll_timer.start(5 * 1000, self)
        self._mempool_timer.start(10 * 1000, self)

    @property
    def network(self):
        return self._network

    def poll_coins(self):
        qt_core.QMetaObject.invokeMethod(
            self._network,
            "poll_coins",
            qt_core.Qt.QueuedConnection)

    def stop_poll(self):
        self._poll_timer.stop()

    def retrieve_fee(self):
        qt_core.QMetaObject.invokeMethod(
            self._network,
            "retrieve_fee",
            qt_core.Qt.QueuedConnection,)

    def look_for_HD(self):
        from ..ui.gui import Application
        for coin in Application.instance().coinList:
            #log.debug(f"Looking for HD chain: {coin}")
            self.lookForHDChain.emit(coin)

    def unspent_list(self, address):
        if address.wants_update_unspents:
            self.unspentsOfWallet.emit(address)

    def update_wallet(self, wallet):
        self.updateAddress.emit(wallet)
