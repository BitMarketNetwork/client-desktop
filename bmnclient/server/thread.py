import threading
import PySide2.QtCore as qt_core


class ServerThread(qt_core.QThread):
    mempoolEveryCoin = qt_core.Signal()

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
                self._poll_timer.start(10 * 10000, self)
        elif event.timerId() == self._mempool_timer.timerId():
            self.mempoolEveryCoin.emit()

    def startTimers(self):
        self._poll_timer.short = True
        self._poll_timer.start(3 * 1000, self)
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
