# JOK4
from __future__ import annotations

import signal
import sys
from socket import SOCK_STREAM, socketpair
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    QObject, \
    Signal as QSignal
from PySide2.QtNetwork import QAbstractSocket

from .logger import Logger
from .os_environment import Platform

if TYPE_CHECKING:
    from typing import Final


class SignalHandler(QObject):
    sighupSignal: Final = QSignal()
    sigintSignal: Final = QSignal()
    sigquitSignal: Final = QSignal()
    sigtermSignal: Final = QSignal()

    if Platform.isWindows:
        _SIGNAL_LIST: Final = (
            (signal.SIGINT, "sigintSignal"),
            (signal.SIGTERM, "sigtermSignal"),
        )
    elif Platform.isDarwin or Platform.isLinux:
        _SIGNAL_LIST: Final = (
            (signal.SIGHUP, "sighupSignal"),
            (signal.SIGINT, "sigintSignal"),
            (signal.SIGQUIT, "sigquitSignal"),
            (signal.SIGTERM, "sigtermSignal"),
        )
    else:
        raise RuntimeError("unsupported platform '{}'".format(Platform.type))

    def __init__(self) -> None:
        super().__init__()
        self._logger = Logger.classLogger(self.__class__)

        read_socket, self._write_socket = socketpair(type=SOCK_STREAM)
        read_socket.setblocking(False)
        self._write_socket.setblocking(False)

        # noinspection PyTypeChecker
        self._qt_socket = QAbstractSocket(QAbstractSocket.TcpSocket, None)
        self._qt_socket.setSocketDescriptor(
            read_socket.detach(),
            openMode=QAbstractSocket.ReadOnly)
        self._qt_socket.readyRead.connect(self._onReadSignal)

        self._old_wakeup_fd = signal.set_wakeup_fd(self._write_socket.fileno())

        self._old_signal_list = [-1] * len(self._SIGNAL_LIST)
        for i in range(len(self._SIGNAL_LIST)):
            self._old_signal_list[i] = signal.signal(
                self._SIGNAL_LIST[i][0],
                self._defaultHandler)
            assert self._old_signal_list[i] != -1

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if self._old_signal_list is not None:
            for i in range(len(self._SIGNAL_LIST)):
                if self._old_signal_list[i] != -1:
                    signal.signal(
                        self._SIGNAL_LIST[i][0],
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

    def _onReadSignal(self) -> None:
        while True:
            sig = self._qt_socket.read(1).data()
            if not len(sig):
                break
            sig = int.from_bytes(sig, sys.byteorder)
            found = False
            for known_signal in self._SIGNAL_LIST:
                if sig == known_signal[0]:
                    self._logger.debug("%s", str(known_signal[0]))
                    getattr(self, known_signal[1]).emit()
                    found = True
                    break
            if not found:
                self._logger.debug(
                    "Unsupported signal %i received.", sig)

    def _defaultHandler(self, sig: int, frame: object) -> None:
        pass
