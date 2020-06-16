
import logging
import functools
from typing import List, Optional
import PySide2.QtCore as qt_core
from .wallet import coins
from .wallet import address
from .wallet import util
from .wallet import serialization
from .wallet import fee_manager
from .wallet.database import database
from .wallet import thread as w_thread
from .server import thread as n_thread
from .server import network
from .config import version as e_config_version
from . import key_manager
from . import debug_manager
from . import signal_handler
from .ui.gui import api

log = logging.getLogger(__name__)


class GcdError(Exception):
    pass


class GCDImpl(qt_core.QObject):

    POLLING_SERVER_LONG_TIMEOUT = 10000
    POLLING_SERVER_SHORT_TIMEOUT = 3000
    # TMP_HASH_FILE = "hash.dat"
    HASH_KEY = "hash"
    SALT_KEY = "salt"

    def __init__(self, silent_mode, parent=None):
        super().__init__(parent=parent)
        self._silent_mode = silent_mode
        self._poll_timer = qt_core.QBasicTimer()
        self._server_version = None
        self._remote_server_version = None
        self.app = None
        self._debug_man = debug_manager.DebugManager(self)
        self._key_manager = key_manager.KeyManager(self)
        self._fee_manager = fee_manager.FeeManager(self)
        #
        self._btc_coin = coins.BitCoin(self)
        self._btc_test_coin = coins.BitCoinTest(self)
        self._ltc_coin = coins.LiteCoin(self)
        self._ltc_test_coin = coins.LiteCoinTest(self)
        self._eth_coin = coins.EthereumCoin(self)
        self._bnb_coin = coins.BinanceCoin(self)
        self._xrp_coin = coins.RippleCoin(self)
        self._xlm_coin = coins.StellarCoin(self)
        self._usdt_coin = coins.TetherCoin(self)
        self._eos_coin = coins.EOSCoin(self)
        self._all_coins = [
            self._btc_coin,
            self._btc_test_coin,
            self._ltc_coin,
            # self._ltc_test_coin,
            self._eth_coin,
            self._bnb_coin,
            self._xrp_coin,
            self._xlm_coin,
            self._usdt_coin,
            self._eos_coin,
        ]
        self._passphrase = None
        self._salt = None
        # self._read_password()
        self._connect_coins()

    def start_threads(self, app: qt_core.QCoreApplication):
        self.app = app
        self.wallet_thread = w_thread.WalletThread(self)
        self.wallet_thread.start()
        self.server_thread = n_thread.ServerThread(self)
        self.server_thread.start()
        self._signal_handler = signal_handler.SignalHandler(self)
        # self.run_ui()
        # this way is preferrable even from the same thread
        qt_core.QMetaObject.invokeMethod(
            self,
            "run_ui",
            qt_core.Qt.QueuedConnection,
        )

    def stop_threads(self):
        self.server_thread.quit()
        self.server_thread.wait()
        self.wallet_thread.quit()
        self.wallet_thread.wait()

    @property
    def network(self) -> network.Network:
        return self.server_thread.network

    @property
    def database(self) -> database.DbWrapper:
        return self.wallet_thread.database

    def _connect_coins(self):
        for coin in self._all_coins:
            coin.statusChanged.connect(
                functools.partial(self._coin_status_changed, coin), qt_core.Qt.UniqueConnection)
            coin.heightChanged.connect(
                functools.partial(self._coin_height_changed, coin), qt_core.Qt.UniqueConnection)


    def save_coins(self):
        qt_core.QMetaObject.invokeMethod(
            self.wallet_thread.database,
            "save_coins",
            qt_core.Qt.QueuedConnection,
        )

    def save_coins_with_addresses(self):
        qt_core.QMetaObject.invokeMethod(
            self.wallet_thread.database,
            "save_coins_with_addresses",
            qt_core.Qt.QueuedConnection,
        )

    def save_coins_settings(self):
        qt_core.QMetaObject.invokeMethod(
            self.wallet_thread.database,
            "save_coins_settings",
            qt_core.Qt.QueuedConnection,
        )

    def retrieve_fee(self):
        qt_core.QMetaObject.invokeMethod(
            self.network,
            "retrieve_fee",
            qt_core.Qt.QueuedConnection,
        )

    def _coin_status_changed(self, coin: coins.CoinType):
        log.debug(F"Coin status changed for {coin}")
        # TODO:

    def _coin_height_changed(self, coin: coins.CoinType):
        # log.info(f"Coin height changed for {coin} to {coin.height}")
        self.retrieveCoinHistory.emit(coin)

    def _check_address_exists(self, address: str) -> bool:
        return any(address.strip().casefold() == n.sacefold() for n in self)

    # Qt override
    def timerEvent(self, event: qt_core.QTimerEvent):
        """
        poll coins' state for new tx if any only we're not busy
        """
        if event.timerId() == self._poll_timer.timerId():
            # TODO: there no point asking server without data .. but it's not for sure !!! tough issue ...
            # if  not self.server_thread.network.busy and self._passphrase is not None:
            if  not self.server_thread.network.busy:
                self.poll_coins()
                if self._poll_timer.short:
                    log.debug("increase polling timeout")
                    self._poll_timer.short = False
                    self._poll_timer.start(
                        self.POLLING_SERVER_LONG_TIMEOUT, self)
        elif event.timerId() == self._save_address_timer.timerId():
            self.save_wallet(self._save_address_timer.wallet)

    @property
    def wallets(self) -> List[address.CAddress]:
        return self._wallet_list

    @property
    def ltc_coin(self) -> coins.CoinType:
        return self._ltc_coin

    @property
    def btc_coin(self) -> coins.CoinType:
        return self._btc_coin

    @property
    def all_coins(self) -> List[coins.CoinType]:
        return self._all_coins

    @property
    def all_visible_coins(self) -> List[coins.CoinType]:
        return [c for c in self._all_coins if c.visible and c.enabled]

    @property
    def all_enabled_coins(self) -> List[coins.CoinType]:
        return [c for c in self._all_coins if c.enabled]

    def get_coin_name(self, coin_tag: str) -> Optional[str]:
        return next((c.fullName for c in self._all_coins if c.name == coin_tag), None)

    @property
    def server_version(self) -> str:
        return self._server_version

    @property
    def db_query_count(self) -> int:
        return self.wallet_thread.database.query_count

    def _get_silent_mode(self) -> bool:
        return self._silent_mode

    def _set_silent_mode(self, mode: bool):
        self._silent_mode = mode

    silent_mode = property(_get_silent_mode, _set_silent_mode)

    @property
    def debug_man(self) -> debug_manager.DebugManager:
        return self._debug_man

    @property
    def key_man(self) -> key_manager.KeyManager:
        return self._key_manager

    @property
    def fee_man(self) -> fee_manager.FeeManager:
        return self._fee_manager

    @property
    def passphrase(self) -> bytes:
        return self._passphrase

    @property
    def salt(self) -> bytes:
        return self._passphrase

    @property
    def is_valid(self):
        "May be more conditions here"
        if self._remote_server_version is None:
            return True
        return self._server_version == self._remote_server_version

    def dump_server_version(self):
        if self._remote_server_version:
            self._server_version = self._remote_server_version
            if self.wallet_thread.ready:
                qt_core.QMetaObject.invokeMethod(
                    self.database,
                    "write_server_version",
                    qt_core.Qt.QueuedConnection,
                )
            else:
                log.warning("DB isn't ready yet")
        else:
            log.warn("Local server version match with remote one")

    @qt_core.Slot(int, str)
    def onServerVersion(self, version: int, human_version: str):
        """
        we got remote version
        if we have version in DB then test it and swear
        else just save it as actual one
        """
        log.debug(f"server version {version} / {human_version}")
        if self._server_version is None or int(version) != int(self._server_version):
            self._remote_server_version = version
            gui = api.Api.get_instance()
            if gui:
                gui.get_instance().uiManager.serverVersion = human_version
            if self._server_version is None:
                self.dump_server_version()
            else:
                log.error("Server version mismatch !!! Client version: %s <> Server version:%s",
                          self._server_version, version)

    def __iter__(self):
        """
        by wallets of all enabled coins
        """
        self._coin_iter = iter(self.all_enabled_coins)
        self._wallet_iter = iter(next(self._coin_iter))
        return self

    def __next__(self):
        try:
            return next(self._wallet_iter)
        except StopIteration:
            self._wallet_iter = iter(next(self._coin_iter))
            return next(self._wallet_iter)

    def export_wallet(self, fpath: str):
        password = self.passphrase
        log.debug(f"Exporting wallet to {fpath} using psw:{password}")
        srl = serialization.Serializator(
            serialization.SerializationType.DEBUG
            | serialization.SerializationType.CYPHER,
            password=password)
        srl.add_one("seed", self._key_manager.master_seed_hex)
        srl.add_many("coins", iter(self._all_coins))
        srl.to_file(fpath)

    def import_wallet(self, fpath: str):
        password = self.passphrase
        log.debug(f"Importing wallet from {fpath} using psw:{password}")
        dsrl = serialization.DeSerializator(fpath, password=password)
        # need to cleanup old stuff
        self.resetDb.emit(self._passphrase)
        self._key_manager.apply_master_seed(
            util.hex_to_bytes(dsrl["seed"]), save=True)
        for coin_t in dsrl["coins"]:
            coin = next(
                (c for c in self._all_coins if c.name == coin_t["name"]), None)
            if coin is not None:
                coin.from_table(coin_t)
            else:
                log.warning(f"Coin {coin_t['name']} isn't found")
        self.save_coins_with_addresses()
        api.Api.get_instance().coinManager.update_coin_model()

    def reset_wallet(self):
        self.dropDb.emit()
        self.remove_password()
        self._server_version = None
        api.Api.get_instance().uiManager.termsApplied = False
        for c in self._all_coins:
            c.clear()

    # def _read_password(self):
    #     try:
    #         with open(self.TMP_HASH_FILE, "rb") as fh: self._passphrase = fh.read().hex()
    #     except:
    #         pass
