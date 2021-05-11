# JOK++
import signal
import socket
import sys
from typing import Optional, Type

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot
from PySide2.QtNetwork import QAbstractSocket

from .logger import Logger
from .platform import Platform


class SignalHandler(QObject):
    SIGHUP = QSignal()
    SIGINT = QSignal()
    SIGQUIT = QSignal()
    SIGTERM = QSignal()

    if Platform.isWindows():
        SIGNAL_LIST = (
            (signal.SIGINT, "SIGINT"),
            (signal.SIGTERM, "SIGTERM"),
        )
    elif Platform.isDarwin() or Platform.isLinux():
        SIGNAL_LIST = (
            (signal.SIGHUP, "SIGHUP"),
            (signal.SIGINT, "SIGINT"),
            (signal.SIGQUIT, "SIGQUIT"),
            (signal.SIGTERM, "SIGTERM"),
        )
    else:
        raise RuntimeError("unsupported platform '{}'".format(Platform.TYPE))

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)
        self._logger = Logger.getClassLogger(__name__, self.__class__)

        read_socket, self._write_socket = socket.socketpair(
            type=socket.SOCK_STREAM)
        read_socket.setblocking(False)
        self._write_socket.setblocking(False)

        self._qt_socket = QAbstractSocket(QAbstractSocket.TcpSocket, self)
        self._qt_socket.setSocketDescriptor(
            read_socket.detach(),
            openMode=QAbstractSocket.ReadOnly)
        self._qt_socket.readyRead.connect(self._onReadSignal)

        self._old_wakeup_fd = signal.set_wakeup_fd(self._write_socket.fileno())

        self._old_signal_list = [-1] * len(self.SIGNAL_LIST)
        for i in range(len(self.SIGNAL_LIST)):
            self._old_signal_list[i] = signal.signal(
                self.SIGNAL_LIST[i][0],
                self._defaultHandler)
            assert self._old_signal_list[i] != -1

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if self._old_signal_list is not None:
            for i in range(len(self.SIGNAL_LIST)):
                if self._old_signal_list[i] != -1:
                    signal.signal(
                        self.SIGNAL_LIST[i][0],
                        self._old_signal_list[i])
            self._old_signal_list = None

        if self._old_wakeup_fd is not None:
            signal.set_wakeup_fd(self._old_wakeup_fd)
            self._old_wakeup_fd = None

        if self._qt_socket is not None:
            self._qt_socket.close()
            self._qt_socket = None

        if self._write_socket is not None:
            self._write_socket.close()
            self._write_socket = None

    @QSlot()
    def _onReadSignal(self) -> None:
        while True:
            sig = self._qt_socket.readData(1)
            if not isinstance(sig, str) or len(sig) == 0:
                break
            sig = int.from_bytes(sig.encode("ascii"), sys.byteorder)
            found = False
            for known_signal in self.SIGNAL_LIST:
                if sig == known_signal[0]:
                    self._logger.debug("%s", known_signal[1])
                    getattr(self, known_signal[1]).emit()
                    found = True
                    break
            if not found:
                self._logger.debug(
                    "Unsupported signal %i received.", sig)

    def _defaultHandler(self, sig: int, frame: Type) -> None:
        pass
