import logging
import os
import pathlib

import PySide2.QtCore as qt_core
import PySide2.QtGui as qt_gui

from client.wallet import aes

from . import gcd_impl as impl
from .gcd_impl import GcdError
from .server import network
from .ui import AppBase as config
from .ui.gui import api
from .wallet import address, coins, mutable_tx, tx, util, key_derivation

log = logging.getLogger(__name__)


class GCD(impl.GCDImpl):
    saveCoin = qt_core.Signal(coins.CoinType, arguments=["coin"])
    lookForHDChain = qt_core.Signal(coins.CoinType, arguments=["coin"])
    saveAddress = qt_core.Signal(
        address.CAddress, int, arguments=["wallet", "timeout"])
    updateAddress = qt_core.Signal(address.CAddress, arguments=["wallet"])
    mempoolAddress = qt_core.Signal(address.CAddress, arguments=["wallet"])
    mempoolCoin = qt_core.Signal(coins.CoinType, arguments=["coin"])
    eraseWallet = qt_core.Signal(address.CAddress, arguments=["wallet"])
    clearAddressTx = qt_core.Signal(address.CAddress, arguments=["address"])
    unspentsOfWallet = qt_core.Signal(address.CAddress, arguments=["wallet"])
    debugUpdateHistory = qt_core.Signal(address.CAddress, arguments=["wallet"])
    retrieveCoinHistory = qt_core.Signal(coins.CoinType, arguments=["coin"])
    netError = qt_core.Signal(int, str, arguments=["code,error"])
    dropDb = qt_core.Signal()
    resetDb = qt_core.Signal(bytes, arguments=["password" ])
    broadcastMtx = qt_core.Signal(
        mutable_tx.MutableTransaction, arguments=["mtx"])
    saveTx = qt_core.Signal(tx.Transaction, arguments=["tx"])
    lockUI = qt_core.Signal(bool, arguments=["on"])
    reloadQml = qt_core.Signal()
    # TODO: connect it
    updateTxs = qt_core.Signal(address.CAddress, arguments=["wallet"])
    saveMeta = qt_core.Signal(str, str, arguments=["name", "value"])
    testPassword = qt_core.Signal(str, arguments=["password", ])
    changePassword = qt_core.Signal(
        bytes, bytes, arguments=["password", "nonce"])

    def __init__(self, silent_mode: bool, parent=None):
        assert isinstance(silent_mode, bool)
        self.__class__.__instance = self
        super().__init__(silent_mode, parent=parent)
        self._ui_started = False

    @classmethod
    def get_instance(cls):
        # take care of the test ( test_tr )
        return getattr(cls, "_GCD__instance", None)
        # return cls.__instance

    def exec_(self):
        # self.lockUI.emit(True)
        return self.app.exec_()

    def serverInfo(self):
        # TODO:
        self._network.server_sysinfo()

    def hide_spinner(self):
        self.lockUI.emit(False)

    def coins_info(self):
        self._network.coins_info()

    def check_tx_count(self):
        if self._btc_address:
            qt_core.QMetaObject.invokeMethod(
                self.wallet_thread.database,
                "check_tx_saved",
                qt_core.Qt.QueuedConnection
            )

    def add_address(self, address: str, coin_str: str = None, coin: coins.CoinType = None):
        if coin is None:
            coin = next((c for c in self.all_coins if c.match(coin_str)), None)
            if coin is None:
                raise impl.GcdError(
                    self.tr(f"There's no coin found matching '{coin}'"))
        # create it
        wallet = coin.append_address(address)
        # why do we save it? we'll save it after update
        # self.save_wallet.emit(wallet)
        # update from server
        self.updateAddress.emit(wallet)

    def save_wallet(self, wallet: address.CAddress, delay_ms: int = None):
        self.saveAddress.emit(wallet, delay_ms)

    def poll_coins(self):
        qt_core.QMetaObject.invokeMethod(
            self.network,
            "poll_coins",
            qt_core.Qt.QueuedConnection,
        )
        #  self.network.poll_coins()

    def get_address_info(self, wallet_pref):
        self._network.wallet_info(self.select_wallet(wallet_pref))

    def get_address_history(self, wallet_pref, **kwargs):
        self._network.wallet_history(self.select_wallet(wallet_pref))

    def save_meta(self, key: str, value: str):
        self.saveMeta.emit(key, value)

    @qt_core.Slot(address.CAddress)
    def update_wallet(self, wallet):
        """
        don't be confused with poll_coins !!! they have different meaning !
        """
        # assert qt_core.QThread.currentThread() == self.thread()
        self.updateTxs.emit(wallet)
        if not self._silent_mode:
            self.updateAddress.emit(wallet)

    def update_wallets(self):
        for addr in self:
            self.update_wallet(addr)

    def select_wallet(self, pref: str):
        return next(w for w in self if w.match(pref))

    def get_coin(self, name: str):
        """
        Get coin by short name
        """
        try:
            return next(c for c in self.all_coins if c.name == name)
        except StopIteration:
            # Keep silence
            log.critical(f"No such coin:{name}")

    def quit(self, exit_code):
        log.debug(f"GCD QUIT with code:{exit_code}")
        qt_core.QCoreApplication.instance().quit()
        self.release()

    def release(self):
        self.stop_poll()
        qt_core.QMetaObject.invokeMethod(
            self.network,
            "abort",
            qt_core.Qt.QueuedConnection,
        )
        qt_core.QMetaObject.invokeMethod(
            self.database,
            "abort",
            qt_core.Qt.QueuedConnection,
        )
        for win in qt_gui.QGuiApplication.topLevelWindows():
            win.close()
        self.stop_threads()

    def stop_poll(self):
        self._poll_timer.stop()

    def retrieve_coin_rates(self):
        qt_core.QMetaObject.invokeMethod(
            self.network,
            "retrieve_rates",
            qt_core.Qt.QueuedConnection,
        )

    def delete_wallet(self, wallet):
        wallet.coin.expanded = False
        self.eraseWallet.emit(wallet)
        wallet.coin.remove_wallet(wallet)

    def delete_all_wallets(self):
        """
        put it to list at first!!
        """
        wlist = [w for w in self]
        for w in wlist:
            self.delete_wallet(w)
        assert self.empty

    @property
    def empty(self):
        return all(len(c) == 0 for c in self._all_coins)

    def process_all_txs(self):
        for w in self:
            for tx_ in w.txs:
                tx_.process()

    def unspent_list(self, address):
        if address.wants_update_unspents:
            self.unspentsOfWallet.emit(address)

    def save_master_seed(self, seed):
        self.saveMeta.emit("seed", seed)

    @qt_core.Slot(str, str)
    def onMeta(self, key: str, value: str):
        log.debug(f"meta value read: {key} => {value}")
        gui_api = api.Api.get_instance()
        if key == "seed":
            if value:
                self._key_manager.apply_master_seed(
                    util.hex_to_bytes(value), save=False)
            else:
                log.debug(f"No master then request it")
                self._key_manager.mnemoRequested.emit()
        elif key == "terms":
            if gui_api:
                gui_api.uiManager.termsApplied = value
        elif key == "language":
            if gui_api:
                gui_api.settingsManager.set_language(value)
        elif key == "base_unit":
            if gui_api and value:
                gui_api.settingsManager.unitIndex = value
        elif key == "style":
            # disable style change for a while
            """
            if gui_api:
                gui_api.settingsManager.styleIndex = value
                self.app.run(value)
            """
        elif key == "font":
            if gui_api:
                gui_api.settingsManager.set_font_from_hex(value)
        else:
            log.error(f"Unknown meta key read: {key}")

    @property
    def first_test_address(self) -> address.CAddress:
        if not self._btc_test_coin.wallets:
            raise RuntimeError("Create any btc test address")
        return self._btc_test_coin.wallets[0]  # pylint: disable=unsubscriptable-object

    def clear_transactions(self, address):
        address.clear()
        self.clearAddressTx.emit(address)
        self.saveAddress.emit(address, None)

    def set_password(self, password: str) -> None:
        impl = key_derivation.KeyDerivation(password)
        qt_core.QSettings(self).setValue(self.HASH_KEY, impl.encode().hex())
        self._salt = os.urandom(16)
        qt_core.QSettings(self).setValue(self.SALT_KEY, self._salt.hex())
        # with open(self.TMP_HASH_FILE, "wb") as fh:
        # fh.write(impl.encode())

    def test_password(self, password: str) -> bool:
        "This supposed to be a hash - not a real password"
        impl = key_derivation.KeyDerivation(password)
        try:
            # with open(self.TMP_HASH_FILE, "rb") as fh:
            if impl.check(bytes.fromhex(
                    qt_core.QSettings(self).value(self.HASH_KEY, "ff"))):
                self._passphrase = impl.value()
                return True
        except Exception as ex:
            log.error(ex)
            pass
        self._passphrase = None
        return False

    def apply_password(self, password: str) -> None:
        """
        """
        self._salt = bytes.fromhex(
            qt_core.QSettings(self).value(self.SALT_KEY, "ff"))
        self.changePassword.emit(self._passphrase , self._salt)
        qt_core.QMetaObject.invokeMethod(
            self,
            "run_user",
            qt_core.Qt.QueuedConnection,
        )

    def has_password(self) -> bool:
        # return pathlib.Path(self.).exists()
        return qt_core.QSettings(self).contains(self.HASH_KEY)

    def remove_password(self) -> None:
        # don't use self api !!
        self.dropDb.emit()
        self._passphrase = None
        self._salt = None
        sett = qt_core.QSettings(self)
        sett.remove(self.HASH_KEY)
        sett.remove(self.SALT_KEY)

    @qt_core.Slot()
    def run_user(self):
        if not self._silent_mode:
            # one trick here - we chould make first call as soon as possible
            # see event for details
            self._poll_timer.short = True
            self._poll_timer.start(self.POLLING_SERVER_SHORT_TIMEOUT, self)

    @qt_core.Slot()
    def run_ui(self):
        if not self._ui_started:
            self._ui_started = True
            self.hide_spinner()
            self.app.run(None)

    def lookForHDChains(self):
        for coin in self.all_enabled_coins:
            log.debug(f"Looking for HD chain: {coin}")
            self.lookForHDChain.emit(coin)
