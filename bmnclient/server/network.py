import logging
from typing import Callable, Optional

import PySide2.QtCore as qt_core

from bmnclient.wallet import address, mutable_tx
from . import debug_cmd, net_cmd
from .. import loading_level
from ..network.query import AbstractQuery
from ..network.query_manager import NetworkQueryManager
from ..wallet import fee_manager

log = logging.getLogger(__name__)


class Network(NetworkQueryManager):
    def __init__(self, parent) -> None:
        super().__init__("Default")
        from ..ui.gui import Application

        self.__cmd = None
        self.__cmd_queue = []
        self.__in_progress = False
        self._cmd_timer = qt_core.QBasicTimer()
        self._fee_timer = qt_core.QBasicTimer()
        self._fee_timer.start(fee_manager.UPDATE_FEE_TIMEOUT, self)
        self.__level_loaded = loading_level.LoadingLevel.NONE
        self.start()

        parent.updateAddress.connect(
            self.update_address, qt_core.Qt.QueuedConnection)
        parent.unspentsOfWallet.connect(
            self.wallet_utxo_list, qt_core.Qt.QueuedConnection)
        parent.mempoolCoin.connect(
            self.retreive_mempool_coin, qt_core.Qt.QueuedConnection)
        parent.mempoolEveryCoin.connect(
            self.retreive_mempool, qt_core.Qt.QueuedConnection)
        parent.broadcastMtx.connect(
            self.broadcast_tx, qt_core.Qt.QueuedConnection)
        parent.lookForHDChain.connect(
            self.look_for_hd_addresses, qt_core.Qt.QueuedConnection)
        parent.undoTx.connect(
            self.undo_tx, qt_core.Qt.QueuedConnection)
        Application.instance().databaseThread.dbLoaded.connect(
            self.level_loaded, qt_core.Qt.QueuedConnection)

        self._run_cmd(net_cmd.CheckServerVersionCommand(self))

    def start(self):
        self._cmd_timer.start(1000, self)

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
        self.__reply.errorOccurred.connect(self.__errorOccurred)
        self.__reply.readyRead.connect(self.__reply_read)
        self.__reply.finished.connect(self.__reply_finished)
        self.__reply.sslErrors.connect(self.__on_ssl_errors)

    def __errorOccurred(self, code):
        pass

    def push_cmd(self, cmd: net_cmd.BaseNetworkCommand, first: bool = False) -> None:
        if first or cmd.high_priority:
            self.__cmd_queue.insert(0, cmd)
        else:
            if cmd.unique and any(isinstance(c, type(cmd)) for c in self.__cmd_queue):
                log.warning(f"unique cmd: {cmd} already present")
                return

            if not cmd.low_priority:
                for i, icmd in enumerate(reversed(self.__cmd_queue)):
                    if not icmd.low_priority:
                        if i:
                            self.__cmd_queue.insert(len(self.__cmd_queue) - i, cmd)
                        else:
                            self.__cmd_queue += [cmd]
                        return
                if self.__cmd_queue:
                    self.__cmd_queue.insert(0, cmd)
                    return
            self.__cmd_queue += [cmd]

    def _run_cmd(
            self,
            cmd: net_cmd.BaseNetworkCommand,
            from_queue: bool = False,
            run_first: bool = False,
            complete_callback: Optional[Callable[[net_cmd.BaseNetworkCommand], None]] = None):
        if cmd.skip:
            return

        # TODO tmp
        if complete_callback:
            cmd.complete_callback = complete_callback

        run_first = run_first or cmd.high_priority
        if self.__in_progress or cmd.level > self.__level_loaded:
            self.push_cmd(cmd, run_first)
        elif not from_queue and not run_first and self.__cmd_queue:
            self.push_cmd(cmd)
            return self.__run_next_cmd()
        else:
            log.debug(f"cmd to run: {cmd}")
            self.__cmd = cmd
            # when we statrt to get history then go out from starting mode
            self.__in_progress = True
            # the most frequent case
            if cmd.method == net_cmd.HttpMethod.GET:
                return self.__make_get_reply(
                    cmd.get_action(),
                    cmd.args,
                    cmd.createRequestData(),  # TODO if None
                    cmd.verbose,
                    cmd.url,
                    **cmd.request_dict)
            if cmd.method == net_cmd.HttpMethod.POST:
                return self.__make_post_reply(
                    cmd.get_action(),
                    cmd.args,
                    cmd.createRequestData(),   # TODO if None
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

        if not self.__cmd.ext:
            from ..application import CoreApplication
            if ok:
                CoreApplication.instance().networkThread.netError.emit(0, "")
            else:
                CoreApplication.instance().networkThread.netError.emit(
                    http_error, self.__reply.errorString())
        del self.__reply
        self.__in_progress = False

        self.__cmd.onResponseFinished()
        if hasattr(self.__cmd, "complete_callback"):
            self.__cmd.complete_callback(self.__cmd)

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
        log.warning('next SSL errors ignored: %s', errors)
        self.__reply.ignoreSslErrors(errors)

    def look_for_hd_addresses(self, coin: "CoinType"):
        self._run_cmd(net_cmd.LookForHDAddresses(coin, self))

    def retreive_mempool_coin(self, coin: "CoinType"):
        self._run_cmd(net_cmd.AddressMultyMempoolCommand(coin.addressList, self))

    def retreive_mempool(self):
        from ..application import CoreApplication
        for c in CoreApplication.instance().coinList:
            self._run_cmd(net_cmd.MempoolMonitorCommand(c, self))

    def undo_tx(self, coin: "CoinType", count: int) -> None:
        self._run_cmd(debug_cmd.UndoTransactionCommand(coin, count, self))

    def level_loaded(self, level: int):
        self.__level_loaded = level

    def wallet_utxo_list(self, wallet):
        self._run_cmd(net_cmd.AddressUnspentCommand(wallet, parent=self))

    def broadcast_tx(self, mtx: mutable_tx.MutableTransaction):
        self._run_cmd(net_cmd.BroadcastTxCommand(mtx, parent=self))

    def update_address(self, wallet: address.CAddress):
        self._run_cmd(net_cmd.UpdateAddressInfoCommand(wallet, self))

    @qt_core.Slot()
    def poll_coins(self):
        self._run_cmd(net_cmd.CheckServerVersionCommand(self))
        self._run_cmd(net_cmd.UpdateCoinsInfoCommand(True, self), run_first=True)

    @qt_core.Slot()
    def retrieve_fee(self):
        self._run_cmd(net_cmd.GetRecommendFeeCommand(parent=self))

    @qt_core.Slot()
    def abort(self):
        log.debug("aborting server")
        self._cmd_timer.stop()
        self._fee_timer.stop()
        reply = getattr(self, '_reply', None)
        if reply:
            reply.abort()
