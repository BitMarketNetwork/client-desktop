import logging
import sqlite3 as sql

import PySide2.QtCore as qt_core

from . import db_wrapper
from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class Database(db_wrapper.DbWrapper, qt_core.QObject):
    def __init__(self, parent):
        self._parent = parent
        super().__init__()
        log.info(f"SQLITE version {sql.sqlite_version}")
        parent.applyPassword.connect(
            self._apply_password, qt_core.Qt.QueuedConnection)

    def _init_actions(self):
        self._parent.saveCoin.connect(
            self._update_coin, qt_core.Qt.QueuedConnection)
        self._parent.saveAddress.connect(
            self._add_or_save_address, qt_core.Qt.QueuedConnection)
        self._parent.saveTx.connect(
            self._write_transaction, qt_core.Qt.QueuedConnection)
        self._parent.dropDb.connect(
            self.drop_db, qt_core.Qt.QueuedConnection)
        self._parent.resetDb.connect(
            self.reset_db, qt_core.Qt.QueuedConnection)
        self.load_everything()

    @qt_core.Slot()
    def close(self):
        self.close_db()

    @qt_core.Slot()
    def save_coins_with_addresses(self):
        # TODO: one query
        from ..application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            self._add_coin(coin, False)
            for address in coin.addressList:
                self._add_or_save_address(address)

    @qt_core.Slot()
    def save_coins_settings(self):
        log.debug("updating all coins in db")
        # TODO: one query
        from ..application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            self._update_coin(coin)

    @qt_core.Slot(AbstractCoin.Address)
    def save_address(self, wallet):
        self._add_or_save_address(wallet, None)

    def load_everything(self) -> None:
        from ..application import CoreApplication
        coins = CoreApplication.instance().coinList

        self._read_all_coins(coins)
        adds = self._read_all_addresses(coins)
        self._read_all_tx(adds)

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._save_address_timer.timerId():
            self._add_or_save_address_impl(self._save_address_timer.wallet)
            self._save_address_timer.stop()
            self._save_address_timer.wallet = None
