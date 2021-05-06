import logging
import sqlite3

from PySide2.QtCore import QObject, Qt, QTimerEvent, Slot as QSlot

from .db_wrapper import DbWrapper
from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class Database(DbWrapper, QObject):
    def __init__(self) -> None:
        super().__init__()
        log.info(f"SQLite version {sqlite3.sqlite_version}")

    @QSlot()
    def close(self) -> None:
        self.close_db()

    @QSlot()
    def save_coins_with_addresses(self) -> None:
        # TODO: one query
        from ..application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            self._add_coin(coin, False)
            for address in coin.addressList:
                self._add_or_save_address(address)

    @QSlot()
    def save_coins_settings(self) -> None:
        log.debug("updating all coins in db")
        # TODO: one query
        from ..application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            self._update_coin(coin)

    @QSlot(AbstractCoin.Address)
    def save_address(self, wallet) -> None:
        self._add_or_save_address(wallet, None)

    def load_everything(self) -> None:
        from ..application import CoreApplication
        coins = CoreApplication.instance().coinList

        self._read_all_coins(coins)
        adds = self._read_all_addresses(coins)
        self._read_all_tx(adds)

    def timerEvent(self, event: QTimerEvent) -> None:
        if event.timerId() == self._save_address_timer.timerId():
            self._add_or_save_address_impl(self._save_address_timer.wallet)
            self._save_address_timer.stop()
            self._save_address_timer.wallet = None
