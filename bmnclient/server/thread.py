import threading
import PySide2.QtCore as qt_core


class ServerThread(qt_core.QThread):
    def __init__(self):
        super().__init__()
        self.finished.connect(self.deleteLater)
        self._network = None

    def run(self):
        threading.current_thread().name = "ServerThread"
        from .network import Network
        self._network = Network()
        self.setPriority(qt_core.QThread.LowPriority)
        # self.finished.connect(self.??.close,    qt_core.Qt.QueuedConnection)
        return self.exec_()

    @property
    def network(self):
        return self._network
