import logging

import PySide2.QtCore as qt_core

from bmnclient.wallet import address, mutable_tx
from . import debug_cmd, net_cmd
from .. import loading_level
from ..network.query_manager import NetworkQueryManager
from ..wallet import fee_manager

log = logging.getLogger(__name__)


class Network(NetworkQueryManager):
    def __init__(self, parent) -> None:
        super().__init__("Default")
        from ..ui.gui import Application

        self.__cmd = None
        self.__cmd_queue = []
        self._fee_timer = qt_core.QBasicTimer()
        self._fee_timer.start(fee_manager.UPDATE_FEE_TIMEOUT, self)
        self.__level_loaded = loading_level.LoadingLevel.NONE

        parent.updateAddress.connect(
            self.update_address, qt_core.Qt.QueuedConnection)
        parent.broadcastMtx.connect(
            self.broadcast_tx, qt_core.Qt.QueuedConnection)
        parent.undoTx.connect(
            self.undo_tx, qt_core.Qt.QueuedConnection)
        Application.instance().databaseThread.dbLoaded.connect(
            self.level_loaded, qt_core.Qt.QueuedConnection)

    def push_cmd(self, cmd: net_cmd.AbstractQuery, first: bool = False) -> None:
        if first:
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

    def _reply_finished(self) -> None:
        http_error = self.__cmd.statusCode
        ok = http_error < 400 or http_error == 500 or http_error == 404
        if not ok:
            log.critical(
                f"HTTP reply error: {self._reply.errorString()} CODE:{http_error}")

        self.__in_progress = False
        self.__cmd.onResponseFinished()

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._fee_timer.timerId():
            self.retrieve_fee()

    def undo_tx(self, coin: "CoinType", count: int) -> None:
        self._run_cmd(debug_cmd.UndoTransactionCommand(coin, count, self))

    def level_loaded(self, level: int):
        self.__level_loaded = level

    def broadcast_tx(self, mtx: mutable_tx.MutableTransaction):
        self._run_cmd(net_cmd.BroadcastTxCommand(mtx, parent=self))

    def update_address(self, wallet: address.CAddress):
        self._run_cmd(net_cmd.AddressInfoApiQuery(wallet, self))

    @qt_core.Slot()
    def retrieve_fee(self):
        self._run_cmd(net_cmd.GetRecommendFeeCommand(parent=self))
