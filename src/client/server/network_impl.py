import logging

import PySide2.QtCore as qt_core
import PySide2.QtNetwork as qt_network

from .url_composer import UrlComposer
from .progress_view import ProgressView
from client.wallet import coins
from client.wallet import address
from client.wallet import tx
from client.config import local as e_config
from client.wallet import fee_manager
from . import net_cmd, debug_cmd

log = logging.getLogger(__name__)


class NetworkImpl(qt_core.QObject):
    API_VERSION = 1
    CMD_DELAY = 100
    REPLY_TIMEOUT = 4000

    def __init__(self, gcd, parent=None):
        super().__init__(parent=parent)
        self._net_manager = qt_network.QNetworkAccessManager(self)
        self._url_manager = UrlComposer(self.API_VERSION)
        self._progress = ProgressView()
        self._cmd = None
        self._gcd = gcd
        self._cmd_queue = []
        self._in_progress = False
        log.info("SSL info: support:%s\tbuild:%s(%s)\tversion:%s(%s)", qt_network.QSslSocket.supportsSsl(), qt_network.QSslSocket.sslLibraryBuildVersionString(), qt_network.QSslSocket.sslLibraryBuildVersionNumber(), qt_network.QSslSocket.sslLibraryVersionString(), qt_network.QSslSocket.sslLibraryVersionNumber()
                 )
        self._cmd_timer = qt_core.QBasicTimer()
        self._reply_timer = qt_core.QBasicTimer()
        self._fee_timer = qt_core.QBasicTimer()
        self._cmd_timer.start(self.CMD_DELAY, self)
        self._fee_timer.start(fee_manager.UPDATE_FEE_TIMEOUT, self)
        # we should be more agile on start
        self._starting_up = True
        self._about_to_quit = False
        self._cui_mode = not e_config.is_gui

    def _make_get_reply(self, action, args, get_args, verbose, ex_host):
        self._reply = self._net_manager.get(
            self._url_manager(action, args=args, gets=get_args, verbose=verbose, ex_host=ex_host,),)
        self._connect_reply(verbose)

    def _make_post_reply(self, action, args, verbose, post_data, **kwargs):
        req = self._url_manager(action, args=args, verbose=verbose)
        log.debug("posting  data: %r", post_data)
        # req.setRawHeader(b"Content-type", b"application/vnd.api+json")
        req.setHeader(qt_network.QNetworkRequest.ContentTypeHeader,
                      "application/vnd.api+json")
        self._reply = self._net_manager.post(req, post_data)
        self._connect_reply(verbose, **kwargs)

    def _connect_reply(self, verbose: bool, **kwargs):
        self._reply.downloadProgress.connect(self._reply_down_progress)
        self._reply.readyRead.connect(self._reply_read)
        self._reply.finished.connect(self._reply_finished)
        self._reply.sslErrors.connect(self._on_ssl_errors)
        if not kwargs.get("test"):
            self._reply_timer.start(self.REPLY_TIMEOUT, self)
            if verbose and self._cui_mode:
                self._progress.reset()

    def coin_address_info(self, wallet: address.CAddress):
        self._run_cmd(net_cmd.AddressInfoCommand(wallet, parent=self))

    def retrieve_address_history(self, wallet: address.CAddress):
        if wallet.isUpdating:
            log.warning(f"skip history request for {wallet}")
            return
        self._run_cmd(net_cmd.AddressHistoryCommand(
            wallet, limit=None, parent=self))

    def _run_cmd(self, cmd):
        if self._in_progress:
            self._cmd_queue += [cmd]
        else:
            log.debug(f"cmd to run:{cmd}")
            cmd.connect_(self._gcd)
            self._cmd = cmd
            # when we statrt to get history then go out from starting mode
            if cmd == net_cmd.AddressHistoryCommand:
                self._starting_up = False
                log.debug(f"Get out from starting mode")
            self._in_progress = True
            # the most frequent case
            if cmd.protocol == net_cmd.HTTPProtocol.GET:
                return self._make_get_reply(cmd.action, cmd.args,
                                            cmd.args_get, cmd.verbose, cmd.host)
            if cmd.protocol == net_cmd.HTTPProtocol.POST:
                return self._make_post_reply(cmd.action, cmd.args,
                                             cmd.verbose, cmd.post_data)
            log.fatal(f"Unsupported HTTP protocol: {cmd.protocol}")

    def _reply_finished(self):
        assert 0 == self._reply.bytesAvailable()
        # for tests
        if self._cmd is None:
            log.critical(f"{self._reply.error()}: {self._reply.errorString()}")
            qt_core.QCoreApplication.instance().quit()
            return
        if self._cmd.verbose and self._cui_mode:
            self._progress.finish()
        http_error = int(self._reply.attribute(
            qt_network.QNetworkRequest.HttpStatusCodeAttribute) or 501)
        ok = http_error < 400 or http_error == 500
        if not ok:
            log.critical(
                f"HTTP reply error: {self._reply.errorString()} CODE:{http_error}")
        # we shouldn't rely on external servers when detect online status
        if not self._cmd.ext:
            if ok:
                self._gcd.netError.emit(0, "")
            else:
                self._gcd.netError.emit(http_error, self._reply.errorString())
        del self._reply
        self._in_progress = False
        if ok:
            _next_cmd = self._cmd.on_data_end(http_error)
            # stick to queue order !
            if _next_cmd:
                self._cmd_queue.append(_next_cmd)
        # dont be so pushy .. give app a little break
        # except we are starting up
        qt_core.QCoreApplication.instance().processEvents(
            qt_core.QEventLoop.ExcludeSocketNotifiers, 50)
        if self._starting_up and self._cmd_queue and not self._about_to_quit:
            self._run_cmd(self._cmd_queue.pop(0))

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._cmd_timer.timerId():
            if not self._in_progress and self._cmd_queue:
                self._run_cmd(self._cmd_queue.pop(0))
        elif event.timerId() == self._reply_timer.timerId():
            if self._in_progress:
                log.warn(
                    f"Drop hanging too long:{self.REPLY_TIMEOUT} reply. command:{self._cmd}")
                self._cmd.drop()
                self._reply.close()
        if event.timerId() == self._fee_timer.timerId():
            self.retrieve_fee()

    def _reply_down_progress(self, rcv, total):
        #log.debug('%s from %s bytes received',rcv,total)
        if self._cui_mode and self._cmd.verbose:
            self._progress(rcv, total)

    def _reply_read(self):
        """
        Do it here to save memory
        There would be multiple calls !!
        """
        if self._cmd:
            self._cmd.on_data(self._reply.readAll())
        else:
            log.debug(self._reply.readAll())

    def _on_ssl_errors(self, errors):
        log.warn('next SSL errors ignored: %s', errors)
        self._reply.ignoreSslErrors(errors)

    def debug_address_history(self, address: "CAddress"):
        cmd = debug_cmd.IncomingTransferCommand(self._gcd, wallet=address)
        cmd.run()

    def look_for_hd_addresses(self, coin: "CoinType"):
        self._run_cmd(net_cmd.LookForHDAddresses(coin, self))

    def retreive_mempool(self, address: "CAddress"):
        self._run_cmd(net_cmd.AddressMempoolCommand(address, self))

    def retreive_mempool_coin(self, coin: "CoinType"):
        self._run_cmd(net_cmd.AddressMultyMempoolCommand( coin.wallets , self))
