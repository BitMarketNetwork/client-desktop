
import logging
import threading
import PySide2.QtCore as qt_core
from .network import Network    
log = logging.getLogger(__name__)

class ServerThread(qt_core.QThread):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.finished.connect(self.deleteLater)
        self._network = None

    def run(self):
        threading.current_thread().name = "ServerThread"
        self._network = Network(gcd = self.parent())
        self.setPriority(qt_core.QThread.LowPriority)
        # self.finished.connect(self.??.close,    qt_core.Qt.QueuedConnection)
        return self.exec_()

    @property
    def network(self):
        return self._network

