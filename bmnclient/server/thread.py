import PySide2.QtCore as qt_core
from ..wallet.coins import CoinType
from ..wallet.address import CAddress
from ..wallet import mutable_tx


class ServerThread(qt_core.QThread):
    mempoolEveryCoin = qt_core.Signal()
    mempoolCoin = qt_core.Signal(CoinType, arguments=["coin"])
    unspentsOfWallet = qt_core.Signal(CAddress, arguments=["wallet"])
    updateAddress = qt_core.Signal(CAddress, arguments=["wallet"])
    undoTx = qt_core.Signal(CoinType, int)
    broadcastMtx = qt_core.Signal(mutable_tx.MutableTransaction, arguments=["mtx"])

    def __init__(self):
        super().__init__()
        self.finished.connect(self.deleteLater)
        self._network = None
        self._mempool_timer = None

    def run(self):
        from .network import Network
        self._mempool_timer = qt_core.QBasicTimer()
        self._network = Network(self)

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._mempool_timer.timerId():
            self.mempoolEveryCoin.emit()

    def startTimers(self):
        self._mempool_timer.start(10 * 1000, self)

    @property
    def network(self):
        return self._network

    def retrieve_fee(self):
        qt_core.QMetaObject.invokeMethod(
            self._network,
            "retrieve_fee",
            qt_core.Qt.QueuedConnection,)

    def unspent_list(self, address):
        if address.wants_update_unspents:
            self.unspentsOfWallet.emit(address)
