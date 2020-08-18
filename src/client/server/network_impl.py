import logging

import PySide2.QtCore as qt_core
import PySide2.QtNetwork as qt_network

from .. import loading_level
from ..config import local as e_config
from ..ui.gui import api
from ..wallet import address, coins, fee_manager, tx
from . import debug_cmd, net_cmd, progress_view, url_composer

log = logging.getLogger(__name__)


class NetworkImpl(qt_core.QObject):
    API_VERSION = 1
    CMD_DELAY = 1000
    REPLY_TIMEOUT = 5000
    EVENTS_QUEUE_LIMIT = 5

    def __init__(self, gcd, parent=None):
        super().__init__(parent=parent)
        self.__net_manager = qt_network.QNetworkAccessManager(self)
        self.__url_manager = url_composer.UrlComposer(self.API_VERSION)
        self.__progress = progress_view.ProgressView()
        self.__cmd = None
        self.__gcd = gcd
        self.__cmd_queue = []
        self.__in_progress = False
        log.info("SSL info: support:%s\tbuild:%s(%s)\tversion:%s(%s)",
                 qt_network.QSslSocket.supportsSsl(),
                 qt_network.QSslSocket.sslLibraryBuildVersionString(),
                 qt_network.QSslSocket.sslLibraryBuildVersionNumber(),
                 qt_network.QSslSocket.sslLibraryVersionString(),
                 qt_network.QSslSocket.sslLibraryVersionNumber()
                 )
        self._cmd_timer = qt_core.QBasicTimer()
        self.__reply_timer = qt_core.QBasicTimer()
        self._fee_timer = qt_core.QBasicTimer()
        self._fee_timer.start(fee_manager.UPDATE_FEE_TIMEOUT, self)
        self.__level_loaded = loading_level.LoadingLevel.NONE
        self.__about_to_quit = False
        self.__cui_mode = not e_config.is_gui
        self._cmd_timer.start(self.CMD_DELAY, self)

    def __make_get_reply(self, action, args, get_args, verbose, ex_host):
        self.__reply = self.__net_manager.get(
            self.__url_manager(action, args=args, gets=get_args, verbose=verbose, ex_host=ex_host,),)
        self.__connect_reply(verbose)

    def __make_post_reply(self, action, args, get_args, verbose, post_data, **kwargs):
        req = self.__url_manager(
            action, args=args, gets=get_args, verbose=verbose)
        log.debug("posting  data: %r", post_data)
        # req.setRawHeader(b"Content-type", b"application/vnd.api+json")
        req.setHeader(qt_network.QNetworkRequest.ContentTypeHeader,
                      "application/vnd.api+json")
        self.__reply = self.__net_manager.post(req, post_data)
        self.__connect_reply(verbose, **kwargs)

    def __connect_reply(self, verbose: bool, **kwargs):
        self.__reply.downloadProgress.connect(self.__reply_down_progress)
        self.__reply.readyRead.connect(self.__reply_read)
        self.__reply.finished.connect(self.__reply_finished)
        self.__reply.sslErrors.connect(self.__on_ssl_errors)
        if not kwargs.get("test"):
            self.__reply_timer.start(self.REPLY_TIMEOUT, self)
            if verbose and self.__cui_mode:
                self.__progress.reset()

    def retrieve_address_history(self, wallet: address.CAddress):
        if wallet.is_going_update:
            log.warning(f"skip history request for {wallet}")
            return
        self._run_cmd(net_cmd.AddressHistoryCommand(
            wallet, limit=None, parent=self, high_priority=True))

    def __push_cmd(self, cmd: net_cmd.AbstractNetworkCommand, first: bool = False) -> None:
        if first or cmd.high_priority:
            self.__cmd_queue.insert(0, cmd)
        else:
            if cmd.unique and any(isinstance(c, type(cmd)) for c in self.__cmd_queue):
                log.warning(f"unique cmd: {cmd} already present")
            elif not cmd.low_priority:
                for i, c in enumerate(reversed(self.__cmd_queue)):
                    # tested!!
                    if not c.low_priority:
                        if i:
                            self.__cmd_queue.insert(
                                len(self.__cmd_queue) - i, cmd)
                        else:
                            self.__cmd_queue += [cmd]
                        break
            else:
                self.__cmd_queue += [cmd]
        # log.critical(f"==> {self.__cmd_queue}")

    def _run_cmd(self, cmd: net_cmd.AbstractNetworkCommand, from_queue: bool = False, run_first: bool = False):
        if cmd.skip:
            return
        run_first = run_first or cmd.high_priority
        if self.__in_progress or cmd.level > self.__level_loaded:
            self.__push_cmd(cmd, run_first)
        elif not from_queue and not run_first and self.__cmd_queue:
            self.__push_cmd(cmd)
            self.__run_next_cmd()
        else:
            if not cmd.silenced:
                log.debug(f"cmd to run:{cmd}")
            cmd.connect_(self.__gcd)
            self.__reply_timer.stop()
            self.__cmd = cmd
            # when we statrt to get history then go out from starting mode
            self.__in_progress = True
            # the most frequent case
            if cmd.protocol == net_cmd.HTTPProtocol.GET:
                return self.__make_get_reply(cmd.get_action(), cmd.args,
                                             cmd.args_get, cmd.verbose, cmd.get_host())
            if cmd.protocol == net_cmd.HTTPProtocol.POST:
                return self.__make_post_reply(cmd.get_action(), cmd.args, cmd.args_get,
                                              cmd.verbose, cmd.post_data)
            log.fatal(f"Unsupported HTTP protocol: {cmd.protocol}")

    def __reply_finished(self):
        if self.__cmd is None:
            log.critical(
                f"{self.__reply.error()}: {self.__reply.errorString()}")
            qt_core.QCoreApplication.instance().quit()
            return
        if self.__cmd.verbose and self.__cui_mode:
            self.__progress.finish()
        http_error = int(self.__reply.attribute(
            qt_network.QNetworkRequest.HttpStatusCodeAttribute) or 501)
        ok = http_error < 400 or http_error == 500 or http_error == 404
        if not ok:
            log.critical(
                f"HTTP reply error: {self.__reply.errorString()} CODE:{http_error}")
        # we shouldn't rely on external servers when detect online status
        if not self.__cmd.ext:
            if ok:
                self.__gcd.netError.emit(0, "")
            else:
                self.__gcd.netError.emit(
                    http_error, self.__reply.errorString())
        del self.__reply
        self.__in_progress = False
        if ok:
            _next_cmd = self.__cmd.on_data_end(http_error)
            # stick to queue order !
            if _next_cmd:
                self.__push_cmd(_next_cmd)
        if self.__cmd_queue and not self.__about_to_quit:
            self.__reply_timer.start(self.CMD_DELAY, self)

    def __run_next_cmd(self):
        while self.__cmd_queue:
            cmd = self.__cmd_queue.pop(0)
            if not cmd.skip:
                self._run_cmd(cmd, from_queue=True)
                break

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._cmd_timer.timerId():
            if not self.__in_progress:
                qt_core.QCoreApplication.processEvents()
                if self.__gcd.post_count < self.EVENTS_QUEUE_LIMIT:
                    self.__run_next_cmd()
        elif event.timerId() == self.__reply_timer.timerId():
            if self.__in_progress:
                log.warn(
                    f"Drop hanging too long:{self.REPLY_TIMEOUT} reply. command:{self.__cmd}")
                self.__cmd.drop()
                if hasattr(self, "__reply"):
                    self.__reply.close()
        if event.timerId() == self._fee_timer.timerId():
            self.retrieve_fee()

    def __reply_down_progress(self, rcv, total):
        # log.debug('%s from %s bytes received',rcv,total)
        if self.__cui_mode and self.__cmd.verbose:
            self.__progress(rcv, total)

    def __reply_read(self):
        """
        Do it here to save memory
        There would be multiple calls !!
        """
        if self.__cmd:
            self.__cmd.on_data(self.__reply.readAll())
        else:
            log.debug(self.__reply.readAll())

    def __on_ssl_errors(self, errors):
        log.warn('next SSL errors ignored: %s', errors)
        self.__reply.ignoreSslErrors(errors)

    def debug_address_history(self, address: "CAddress"):
        cmd = debug_cmd.IncomingTransferCommand(self.__gcd, wallet=address)
        cmd.run()

    def look_for_hd_addresses(self, coin: "CoinType"):
        self._run_cmd(net_cmd.LookForHDAddresses(coin, self))

    def retreive_mempool(self, address: "CAddress"):
        self._run_cmd(net_cmd.AddressMempoolCommand(address, self))

    def retreive_mempool_coin(self, coin: "CoinType"):
        self._run_cmd(net_cmd.AddressMultyMempoolCommand(coin.wallets, self))

    def validate_address(self, coin: "CoinType", address: str):
        def callback(result: bool):
            api_: api.Api = api.Api.get_instance()
            if api_:
                api_.coinManager.address_validated_handler(
                    coin, address, result)
        self._run_cmd(net_cmd.ValidateAddressCommand(
            coin, address, callback, self))

    def undo_tx(self, coin: "CoinType", count: int) -> None:
        self._run_cmd(debug_cmd.UndoTransactionCommand(coin, count, self))

    def http_failure_simulation(self, code: int) -> None:
        self._run_cmd(debug_cmd.HTTPFailureCommand(code, self))

    def fake_mempool_seach(self, tx_: tx.Transaction):
        cmd = debug_cmd.FakeMempoolCommand(tx_, self)
        cmd.connect_(self.__gcd)
        cmd.run()

    def level_loaded(self, level: int):
        self.__level_loaded = level

    @property
    def busy(self):
        return self.__in_progress or self.__cmd_queue
