import PySide2.QtCore as qt_core
from ..wallet.coins import CoinType
from ..wallet.address import CAddress
from ..wallet import mutable_tx


class ServerThread(qt_core.QThread):
    updateAddress = qt_core.Signal(CAddress, arguments=["wallet"])
    undoTx = qt_core.Signal(CoinType, int)
    broadcastMtx = qt_core.Signal(mutable_tx.MutableTransaction, arguments=["mtx"])

    def __init__(self):
        super().__init__()
        self.finished.connect(self.deleteLater)
        from .network import Network
        self._network = Network(self)

    @property
    def network(self):
        return self._network

    def retrieve_fee(self):
        qt_core.QMetaObject.invokeMethod(
            self._network,
            "retrieve_fee",
            qt_core.Qt.QueuedConnection,)
