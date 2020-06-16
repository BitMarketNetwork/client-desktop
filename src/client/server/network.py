import logging
import PySide2.QtCore as qt_core
from . import network_impl
from . import net_cmd
from client.wallet import coins
from client.wallet import address
from client.wallet import tx
from client.wallet import mutable_tx

log = logging.getLogger(__name__)


class Network(network_impl.NetworkImpl):

    def __init__(self, gcd, parent=None):
        super().__init__(gcd, parent=parent)
        # connect
        gcd.updateAddress.connect(
            self.update_address, qt_core.Qt.QueuedConnection)
        gcd.retrieveCoinHistory.connect(
            self.retrieve_coin_history, qt_core.Qt.QueuedConnection)
        gcd.unspentsOfWallet.connect(
            self.wallet_utxo_list, qt_core.Qt.QueuedConnection)
        gcd.mempoolAddress.connect(
            self.retreive_mempool, qt_core.Qt.QueuedConnection)
        gcd.mempoolCoin.connect(
            self.retreive_mempool_coin, qt_core.Qt.QueuedConnection)
        gcd.broadcastMtx.connect(
            self.broadcast_tx, qt_core.Qt.QueuedConnection)
        gcd.debugUpdateHistory.connect(
            self.debug_address_history, qt_core.Qt.QueuedConnection)
        gcd.lookForHDChain.connect(
            self.look_for_hd_addresses, qt_core.Qt.QueuedConnection)
        # #
        self._run_cmd(net_cmd.CheckServerVersionCommand(self))
        self._run_cmd(net_cmd.GetCoinRatesCommand(self))
        # self._run_cmd(net_cmd.UpdateCoinsInfoCommand(False, self))

    def server_sysinfo(self):
        self._run_cmd(net_cmd.ServerSysInfoCommand(self))

    def coins_info(self):
        self._run_cmd(net_cmd.CoinInfoCommand(self))

    def wallet_utxo_list(self, wallet):
        self._run_cmd(net_cmd.AddressUnspentCommand(wallet, parent=self))

    def broadcast_tx(self, mtx: mutable_tx.MutableTransaction):
        self._run_cmd(net_cmd.BroadcastTxCommand(mtx, parent=self))

    def wallet_info(self, wallet):
        self.coin_address_info(wallet)

    def wallet_history(self, wallet):
        self.retrieve_address_history(wallet)

    def update_address(self, wallet: address.CAddress):
        self._run_cmd(net_cmd.UpdateAddressInfoCommand(wallet, self))

    @qt_core.Slot()
    def poll_coins(self):
        self._run_cmd(net_cmd.UpdateCoinsInfoCommand(True, self))

    @qt_core.Slot()
    def retrieve_fee(self):
        self._run_cmd(net_cmd.GetRecommendFeeCommand(parent=self))

    @qt_core.Slot()
    def abort(self):
        log.debug("aborting server")
        self._about_to_quit = True
        self._cmd_timer.stop()
        self._fee_timer.stop()
        reply = getattr(self,'_reply',None)
        if reply:
            reply.abort()

    @qt_core.Slot()
    def retrieve_rates(self):
        self._run_cmd(net_cmd.GetCoinRatesCommand(self))

    def retrieve_coin_history(self, coin: coins.CoinType):
        for wad in coin.wallets:
            # update tx
            self.retrieve_address_history(wad)
            # update balance
            self._run_cmd(net_cmd.UpdateAddressInfoCommand(wad, self))

    @property
    def busy(self):
        # queue is redundant but let's try
        return self._in_progress or self._cmd_queue
