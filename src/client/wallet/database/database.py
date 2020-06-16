import base64
import hashlib
import sys
import logging

import sqlite3 as sql
import PySide2.QtCore as qt_core

from .db_wrapper import DbWrapper
from .. import coins
from .. import address
from .. import tx
from client.ui.gui import api  # pylint; disable=import-error
from client.config import version  # pylint; disable=import-error

log = logging.getLogger(__name__)
SERVER_VERSION_KEY = "server_version"
CLIENT_VERSION_KEY = "client_version"


class Database(DbWrapper, qt_core.QObject):
    dbOpened = qt_core.Signal(bool)
    metaRead = qt_core.Signal(str, str, arguments=["key", "value"])
    testPassword = qt_core.Signal(str)

    def __init__(self, gcd, password: str, parent: qt_core.QObject = None):
        super().__init__(parent=parent)
        log.info(f"SQLITE version {sql.sqlite_version}")
        self._gcd = gcd
        self._gcd.changePassword.connect(
            self._apply_password, qt_core.Qt.QueuedConnection)

    def _init_actions(self):
        if self._gcd:  # it can happen during testing
            assert self._gcd.thread() != self.thread()
            """
            qt_core.QObject.connect(
                self,
                qt_core.SIGNAL("update_wallet()"),
                self._gcd.update_wallet ,
                qt_core.Qt.QueuedConnection
                )
            """
            self._process_client_version()
            self._gcd.saveCoin.connect(
                self._update_coin, qt_core.Qt.QueuedConnection)
            self._gcd.saveAddress.connect(
                self._add_or_save_wallet, qt_core.Qt.QueuedConnection)
            self._gcd.eraseWallet.connect(
                self.erase_wallet, qt_core.Qt.QueuedConnection)
            self._gcd.saveMeta.connect(
                self._set_meta_entry, qt_core.Qt.QueuedConnection)
            self._gcd.saveTx.connect(
                self._write_transaction, qt_core.Qt.QueuedConnection)
            self._gcd.clearAddressTx.connect(
                self._clear_tx, qt_core.Qt.QueuedConnection)
            self._gcd.dropDb.connect(
                self.drop_db, qt_core.Qt.QueuedConnection)
            self._gcd.resetDb.connect(
                self.reset_db, qt_core.Qt.QueuedConnection)
            self._gcd._server_version = self._get_meta_entry(
                SERVER_VERSION_KEY)
            # read mnemonic
            self.metaRead.connect(
                self._gcd.onMeta, qt_core.Qt.QueuedConnection)
            # order makes sense !!!
            self._read_meta("font")
            self._read_meta("style")
            self._read_meta("language")
            self._read_meta("base_unit")
            self._read_meta("seed")
            self._read_meta("terms")
            self.load_everything()

    def _read_meta(self, key: str) -> None:
        self.metaRead.emit(key, self._get_meta_entry(key))

    def _process_client_version(self) -> None:
        client_version = self._get_meta_entry(CLIENT_VERSION_KEY)
        local_client_version = ".".join(map(str, version.CLIENT_VERSION))
        if client_version == local_client_version:
            return
        if not client_version:
            log.warning(f"No client version in DB")
            self._set_meta_entry(CLIENT_VERSION_KEY, local_client_version)
        else:
            # swear here
            log.warning(
                f"DB client version:{client_version} doesn't match code client version: {local_client_version}")
            # self._gcd.quit(1)

    @qt_core.Slot()
    def abort(self):
        log.debug("aborting db")
        self._save_address_timer.stop()

    @qt_core.Slot()
    def close(self):
        self.close_db()

    def is_opened(self):
        return self._conn is not None

    @qt_core.Slot()
    def save_coins(self):
        # TODO: one query
        for coin in self._gcd.all_coins:
            self._add_coin(coin, True)
        self._update_wallets()

    @qt_core.Slot()
    def save_coins_with_addresses(self):
        # TODO: one query
        for coin in self._gcd.all_coins:
            self._add_coin(coin, False)
            for wal in coin.wallets:
                self._add_or_save_wallet(wal)

    @qt_core.Slot()
    def save_coins_settings(self):
        log.debug("updating all coins in db")
        # TODO: one query
        for coin in self._gcd.all_coins:
            self._update_coin(coin)

    @qt_core.Slot(address.CAddress)
    def save_wallet(self, wallet):
        self._add_or_save_wallet(wallet, None)

    @qt_core.Slot(address.CAddress)
    def erase_wallet(self, wallet):
        self._erase_wallet(wallet)

    @qt_core.Slot()
    def write_server_version(self):
        self._set_meta_entry(SERVER_VERSION_KEY, self._gcd.server_version)


    @qt_core.Slot()
    def load_everything(self, coins=None):
        if coins is None:
            coins = self._gcd.all_coins
        self._read_all_coins(coins)
        adds = self._read_all_addresses(coins)
        txs = self._read_all_tx(adds)
        self._read_all_inputs(txs)
        """
        qt_core.QMetaObject.invokeMethod(
            self._gcd,
            "run_ui",
            qt_core.Qt.QueuedConnection,
        )
        """

    def _update_wallets(self):
        qt_core.QMetaObject.invokeMethod(
            self._gcd,
            "update_wallets",
            qt_core.Qt.QueuedConnection
        )
        api_ = api.Api.get_instance()
        # update coins visibility
        if api_ is not None:
            qt_core.QMetaObject.invokeMethod(
                api_.coinManager,
                "coinModelChanged",
                qt_core.Qt.QueuedConnection
            )

    def timerEvent(self, event: qt_core.QTimerEvent):
        if event.timerId() == self._save_address_timer.timerId():
            self._add_or_save_wallet_impl(self._save_address_timer.wallet)
            self._save_address_timer.stop()
            self._save_address_timer.wallet = None

    def __del__(self):
        if self._conn:
            # self._conn.close()
            log.debug('connection is still opened')

    def __bool__(self):
        return self.is_opened()
