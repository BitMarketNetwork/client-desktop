import logging
import sqlite3 as sql

import PySide2.QtCore as qt_core

from . import db_wrapper
from ..wallet import address
from .. import loading_level

log = logging.getLogger(__name__)


class Database(db_wrapper.DbWrapper, qt_core.QObject):
    def __init__(self, parent):
        self._parent = parent
        from ..ui.gui import Application
        super().__init__()
        log.info(f"SQLITE version {sql.sqlite_version}")
        parent.applyPassword.connect(
            self._apply_password, qt_core.Qt.QueuedConnection)

    def _init_actions(self):
        self._parent.saveCoin.connect(
            self._update_coin, qt_core.Qt.QueuedConnection)
        self._parent.saveAddress.connect(
            self._add_or_save_wallet, qt_core.Qt.QueuedConnection)
        self._parent.eraseWallet.connect(
            self.erase_wallet, qt_core.Qt.QueuedConnection)
        self._parent.saveTx.connect(
            self._write_transaction, qt_core.Qt.QueuedConnection)
        self._parent.saveTxList.connect(
            self._write_transactions, qt_core.Qt.QueuedConnection)
        self._parent.removeTxList.connect(
            self._remove_tx_list, qt_core.Qt.QueuedConnection)
        self._parent.clearAddressTx.connect(
            self._clear_tx, qt_core.Qt.QueuedConnection)
        self._parent.dropDb.connect(
            self.drop_db, qt_core.Qt.QueuedConnection)
        self._parent.resetDb.connect(
            self.reset_db, qt_core.Qt.QueuedConnection)
        self.load_everything()

    @qt_core.Slot()
    def abort(self):
        log.warning("aborting db")
        self._save_address_timer.stop()

    @qt_core.Slot()
    def close(self):
        self.close_db()

    @qt_core.Slot()
    def save_coins_with_addresses(self):
        # TODO: one query
        from ..application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            self._add_coin(coin, False)
            for wal in coin.wallets:
                self._add_or_save_wallet(wal)

    @qt_core.Slot()
    def save_coins_settings(self):
        log.debug("updating all coins in db")
        # TODO: one query
        from ..application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            self._update_coin(coin)

    @qt_core.Slot(address.CAddress)
    def save_wallet(self, wallet):
        self._add_or_save_wallet(wallet, None)

    @qt_core.Slot(address.CAddress)
    def erase_wallet(self, wallet):
        self._erase_wallet(wallet)

    # @qt_core.Slot()
    def load_everything(self, coins=None):
        if coins is None:
            from ..application import CoreApplication
            coins = CoreApplication.instance().coinList
        self._read_all_coins(coins)
        adds = self._read_all_addresses(coins)
        self._parent.db_level_loaded(loading_level.LoadingLevel.ADDRESSES)
        txs = self._read_all_tx(adds)
        self._parent.db_level_loaded(loading_level.LoadingLevel.TRANSACTIONS)
        inputs = self._read_all_inputs(txs)
        self._parent.db_level_loaded(loading_level.LoadingLevel.INPUTS)

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._save_address_timer.timerId():
            self._add_or_save_wallet_impl(self._save_address_timer.wallet)
            self._save_address_timer.stop()
            self._save_address_timer.wallet = None
