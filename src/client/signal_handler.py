

import logging
import os
import signal
import struct
import socket
import PySide2.QtCore as qt_core
import PySide2.QtGui as qt_gui
import PySide2.QtNetwork as qt_network
from . import meta
log = logging.getLogger(__name__)


class SignalHandler(qt_core.QObject):

    def __init__(self, parent: qt_core.QObject):
        super().__init__(parent)
        self._handle_unix_signals()

    def _handle_unix_signals(self):
        if not meta.IS_WINDOWS:
            signal.signal(signal.SIGHUP, self.handle_sighup)
        #
        if meta.IS_WINDOWS or meta.IS_OSX:
            # TODO: test this on windows
            self.signal_read_socket, self.signal_write_socket = socket.socketpair()
            self.signal_read_socket.setblocking(False)
            self.signal_write_socket.setblocking(False)
            read_fd, write_fd = self.signal_read_socket.fileno(), self.signal_write_socket.fileno()
        else:
            read_fd, write_fd = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *x: None)
            if not meta.IS_WINDOWS:
                # TODO: don't work on win
                signal.siginterrupt(sig, False)
        signal.set_wakeup_fd(write_fd)
        self.signal_notifier = qt_core.QSocketNotifier(
            read_fd, qt_core.QSocketNotifier.Read, self)
        self.signal_notifier.setEnabled(True)
        self.signal_notifier.activated.connect(
            self.signal_received, type=qt_core.Qt.QueuedConnection)

    def handle_sighup(self, *args):
        log.debug(f"ignoring SIGHUP")

    def signal_received(self, read_fd):
        try:
            data = self.signal_read_socket.recv(
                1024) if meta.IS_WINDOWS else os.read(read_fd, 1024)
        except BlockingIOError:
            return
        if data:
            signals = struct.unpack('%uB' % len(data), data)
            log.debug(f"signals handled: {signals}")
            if not meta.IS_WINDOWS and signal.SIGHUP in signals:
                log.warning(f"sighup detected: skip it")
            elif signal.SIGINT in signals or signal.SIGTERM in signals:
                self.parent().quit(1)
