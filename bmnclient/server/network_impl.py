import logging

import os
import PySide2.QtCore as qt_core
import PySide2.QtNetwork as qt_network
from PySide2.QtNetwork import QNetworkRequest

from .. import loading_level
from ..wallet import address, fee_manager, tx
from . import debug_cmd, net_cmd, progress_view, url_composer
from ..application import CoreApplication
log = logging.getLogger(__name__)


class NetworkImpl(qt_core.QObject):
    def _setResponseStatusCode(self) -> bool:
        if self.__cmd.statusCode is not None:
            return False
        http_status = self.__reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        if not http_status:
            os.abort()
        self.__cmd.statusCode = int(http_status)
        return True



    API_VERSION = 1
    CMD_DELAY = 1000
    REPLY_TIMEOUT = 5000

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # self.__net_manager = qt_network.QNetworkAccessManager(self)
        self.__net_manager = CoreApplication.instance()._qml_network_factory.create(self)
        ##
        self.__url_manager = url_composer.UrlComposer(self.API_VERSION)
        self.__progress = progress_view.ProgressView()
        self.__cmd = None
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
        self._fee_timer = qt_core.QBasicTimer()
        self._fee_timer.start(fee_manager.UPDATE_FEE_TIMEOUT, self)
        self.__level_loaded = loading_level.LoadingLevel.NONE
        self.start()

    def start(self):
        self._cmd_timer.start(self.CMD_DELAY, self)

    def __make_get_reply(self, action, args, get_args, verbose, ex_host, **kwargs):
        req = self.__url_manager(
            action,
            args=args,
            gets=get_args,
            verbose=verbose,
            ex_host=ex_host,
            **kwargs)
        self.__reply = self.__net_manager.get(req)
        self.__connect_reply()
        return req

    def __make_post_reply(self, action, args, get_args, verbose, post_data, **kwargs):
        req = self.__url_manager(
            action, args=args, gets=get_args, verbose=verbose)
        log.debug("posting  data: %r", post_data)
        # req.setRawHeader(b"Content-type", b"application/vnd.api+json")
        req.setHeader(qt_network.QNetworkRequest.ContentTypeHeader,
                      "application/vnd.api+json")
        self.__reply = self.__net_manager.post(req, post_data)
        self.__connect_reply()
        return req

    def __connect_reply(self) -> None:
        self.__reply.readyRead.connect(self.__reply_read)
        self.__reply.finished.connect(self.__reply_finished)
        self.__reply.sslErrors.connect(self.__on_ssl_errors)

    def push_cmd(self, cmd: net_cmd.AbstractNetworkCommand, first: bool = False) -> None:
        if first or cmd.high_priority:
            self.__cmd_queue.insert(0, cmd)
        else:
            if cmd.unique and any(isinstance(c, type(cmd)) for c in self.__cmd_queue):
                log.warning(f"unique cmd: {cmd} already present")
                return
            ##
            if not cmd.low_priority:
                for i, icmd in enumerate(reversed(self.__cmd_queue)):
                    # tested!!
                    if not icmd.low_priority:
                        if i:
                            self.__cmd_queue.insert(
                                len(self.__cmd_queue) - i, cmd)
                        else:
                            self.__cmd_queue += [cmd]
                        return
                if self.__cmd_queue:
                    self.__cmd_queue.insert(0, cmd)
                    return
            self.__cmd_queue += [cmd]
        # log.critical(f"==> {self.__cmd_queue}")

    def _run_cmd(self, cmd: net_cmd.AbstractNetworkCommand, from_queue: bool = False, run_first: bool = False):
        if cmd.skip:
            return
        run_first = run_first or cmd.high_priority
        if self.__in_progress or cmd.level > self.__level_loaded:
            log.debug(f"{cmd}; {cmd.level} > {self.__level_loaded}")
            self.push_cmd(cmd, run_first)
        elif not from_queue and not run_first and self.__cmd_queue:
            self.push_cmd(cmd)
            return self.__run_next_cmd()
        else:
            if not cmd.silenced:
                log.debug(f"cmd to run:{cmd}")
            cmd.connect_()
            self.__cmd = cmd
            # when we statrt to get history then go out from starting mode
            self.__in_progress = True
            # the most frequent case
            if cmd.method == net_cmd.HttpMethod.GET:
                return self.__make_get_reply(
                    cmd.get_action(),
                    cmd.args,
                    cmd.args_get,
                    cmd.verbose,
                    cmd.get_host(),
                    **cmd.request_dict)
            if cmd.method == net_cmd.HttpMethod.POST:
                return self.__make_post_reply(
                    cmd.get_action(),
                    cmd.args,
                    cmd.args_get,
                    cmd.verbose,
                    cmd.post_data,
                    **cmd.request_dict)
            log.fatal(f"Unsupported HTTP method: {cmd.method}")
            return None

    def __reply_read(self) -> None:
        if self.__cmd is None:
            log.warning(self.__reply.readAll())
            return

        self._setResponseStatusCode()
        if not self.__cmd.onResponseData(self.__reply.readAll()):
            self.__reply.abort()

    def __reply_finished(self) -> None:
        if self.__cmd is None:
            log.critical(
                f"{self.__reply.error()}: {self.__reply.errorString()}")
            os.abort()
            return

        self._setResponseStatusCode()
        http_error = self.__cmd.statusCode
        ok = http_error < 400 or http_error == 500 or http_error == 404
        if not ok:
            log.critical(
                f"HTTP reply error: {self.__reply.errorString()} CODE:{http_error}")
        # we shouldn't rely on external servers when detect online status
        if not self.__cmd.ext:
            from ..application import CoreApplication
            if ok:
                CoreApplication.instance().networkThread.netError.emit(0, "")
            else:
                CoreApplication.instance().networkThread.netError.emit(
                    http_error, self.__reply.errorString())
        del self.__reply
        self.__in_progress = False
        if ok:
            self.__cmd.onResponseFinished()

    def __run_next_cmd(self):
        while self.__cmd_queue:
            # log.debug(f"queue len : {len(self.__cmd_queue)}")
            cmd = self.__cmd_queue.pop(0)
            if not cmd.skip:
                return self._run_cmd(cmd, from_queue=True)

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._cmd_timer.timerId():
            if not self.__in_progress:
                qt_core.QCoreApplication.processEvents()
                self.__run_next_cmd()
        if event.timerId() == self._fee_timer.timerId():
            self.retrieve_fee()

    def __on_ssl_errors(self, errors):
        log.warn('next SSL errors ignored: %s', errors)
        self.__reply.ignoreSslErrors(errors)

    def look_for_hd_addresses(self, coin: "CoinType"):
        self._run_cmd(net_cmd.LookForHDAddresses(coin, self))

    def retreive_mempool(self, address: "CAddress"):
        self._run_cmd(net_cmd.AddressMempoolCommand(address, self))

    def retreive_mempool_coin(self, coin: "CoinType"):
        self._run_cmd(net_cmd.AddressMultyMempoolCommand(coin.wallets, self))

    def retreive_mempool(self):
        from ..application import CoreApplication
        for c in CoreApplication.instance().coinList:
            self._run_cmd(net_cmd.MempoolMonitorCommand(c, self))

    def undo_tx(self, coin: "CoinType", count: int) -> None:
        self._run_cmd(debug_cmd.UndoTransactionCommand(coin, count, self))

    def level_loaded(self, level: int):
        self.__level_loaded = level

    @property
    def _queue(self) -> list:
        "access only for tests"
        #assert config.DEBUG_MODE
        return self.__cmd_queue
