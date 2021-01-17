import logging

import PySide2.QtCore as qt_core

from bmnclient.wallet import address, coins, mutable_tx
from . import net_cmd, network_impl

log = logging.getLogger(__name__)


class Network(network_impl.NetworkImpl):
    def __init__(self):
        from ..ui.gui import Application
        gcd = Application.instance().gcd
        super().__init__(gcd)
        # connect
        gcd.updateAddress.connect(
            self.update_address, qt_core.Qt.QueuedConnection)
        gcd.retrieveCoinHistory.connect(
            self.retrieve_coin_history, qt_core.Qt.QueuedConnection)
        gcd.unspentsOfWallet.connect(
            self.wallet_utxo_list, qt_core.Qt.QueuedConnection)
        gcd.mempoolCoin.connect(
            self.retreive_mempool_coin, qt_core.Qt.QueuedConnection)
        gcd.mempoolEveryCoin.connect(
            self.retreive_mempool, qt_core.Qt.QueuedConnection)
        gcd.broadcastMtx.connect(
            self.broadcast_tx, qt_core.Qt.QueuedConnection)
        gcd.debugUpdateHistory.connect(
            self.debug_address_history, qt_core.Qt.QueuedConnection)
        gcd.lookForHDChain.connect(
            self.look_for_hd_addresses, qt_core.Qt.QueuedConnection)
        gcd.validateAddress.connect(
            self.validate_address, qt_core.Qt.QueuedConnection)
        gcd.undoTx.connect(
            self.undo_tx, qt_core.Qt.QueuedConnection)
        gcd.httpFailureSimulation.connect(
            self.http_failure_simulation, qt_core.Qt.QueuedConnection)
        gcd.dbLoaded.connect(
            self.level_loaded, qt_core.Qt.QueuedConnection)
        gcd.fakeMempoolSearch.connect(
            self.fake_mempool_seach, qt_core.Qt.QueuedConnection)
        gcd.addressHistory.connect(
            self.retrieve_address_history, qt_core.Qt.QueuedConnection)
        gcd.startNetwork.connect(
            self.start, qt_core.Qt.QueuedConnection)

        self._run_cmd(net_cmd.CheckServerVersionCommand(self))
        self._run_cmd(net_cmd.GetCoinRatesCommand(self))

    def server_sysinfo(self):
        self._run_cmd(net_cmd.ServerSysInfoCommand(self))

    def wallet_utxo_list(self, wallet):
        self._run_cmd(net_cmd.AddressUnspentCommand(wallet, parent=self))

    def broadcast_tx(self, mtx: mutable_tx.MutableTransaction):
        self._run_cmd(net_cmd.BroadcastTxCommand(mtx, parent=self))

    def update_address(self, wallet: address.CAddress):
        self._run_cmd(net_cmd.UpdateAddressInfoCommand(wallet, self))

    @qt_core.Slot()
    def poll_coins(self):
        self._run_cmd(net_cmd.UpdateCoinsInfoCommand(
            True, self), run_first=True)

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

    @qt_core.Slot()
    def retrieve_rates(self):
        self._run_cmd(net_cmd.GetCoinRatesCommand(self))

    def retrieve_coin_history(self, coin: coins.CoinType):
        for wad in coin.wallets:
            # # update tx
            # self.retrieve_address_history(wad)
            # update balance
            self._run_cmd(net_cmd.UpdateAddressInfoCommand(wad, self))
