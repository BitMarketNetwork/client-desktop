
import logging
import PySide2.QtCore as qt_core
from .network import Network    
log = logging.getLogger(__name__)

class ServerThread(qt_core.QThread):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.finished.connect(self.deleteLater)

    def run(self):
        self._network = Network(gcd = self.parent())
        # self.finished.connect(self.??.close,    qt_core.Qt.QueuedConnection)
        return self.exec_()

    @property
    def network(self):
        return self._network

