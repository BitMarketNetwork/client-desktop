
import functools
import logging
import threading
import datetime
from collections import abc
from typing import Any, List, Optional, Type, Union

import PySide2.QtCore as qt_core
import bmnclient.version
import bmnclient.config

from . import debug_manager, signal_handler, meta
from bmnclient import version as e_config_version
from .server import network
from .server import thread as n_thread
from .ui.gui import qml_context
from .wallet import address, coins, fee_manager, serialization
from .wallet import thread as w_thread
from .wallet import util
from .wallet.database import database

log = logging.getLogger(__name__)


class GcdError(Exception):
    pass


class GCDImpl(meta.QSeq):

    POLLING_SERVER_LONG_TIMEOUT = 10000
    POLLING_SERVER_SHORT_TIMEOUT = 3000
    MEMPOOL_MONITOR_TIMEOUT = 60000
    # TMP_HASH_FILE = "hash.dat"

    def __init__(self, silent_mode, parent=None):
        super().__init__(parent=parent)
        self.launch_time = datetime.datetime.utcnow()
        self.silent_mode = silent_mode
        self._mempool_timer = qt_core.QBasicTimer()
        self._poll_timer = qt_core.QBasicTimer()
        self.app = None
        self.__debug_man = debug_manager.DebugManager(self)
        from . import key_manager
        self._key_manager = key_manager.KeyManager(self)
        self.__fee_manager = fee_manager.FeeManager(self)
        #
        self.__btc_coin = coins.BitCoin(self)
        self.__btc_test_coin = coins.BitCoinTest(self)
        self.__ltc_coin = coins.LiteCoin(self)
        self.__eth_coin = coins.EthereumCoin(self)
        self.__bnb_coin = coins.BinanceCoin(self)
        self.__xrp_coin = coins.RippleCoin(self)
        self.__xlm_coin = coins.StellarCoin(self)
        self.__usdt_coin = coins.TetherCoin(self)
        self.__eos_coin = coins.EOSCoin(self)
        self.__all_coins = [
            self.__btc_coin,
            self.__btc_test_coin,
            self.__ltc_coin,
            self.__eth_coin,
            self.__bnb_coin,
            self.__xrp_coin,
            self.__xlm_coin,
            self.__usdt_coin,
            self.__eos_coin,
        ]
        self.__remote_server_version = None
        self._passphrase = None
        self._settings = None
        self.__post_count = 0
        self.__post_mutex = threading.Lock()
        self._mnemo: bytes = None
        self._db_valid = True
        self.__create_settings()
        self.__connect_coins()

    def start_threads(self, app: qt_core.QCoreApplication, run_ui=True):
        self.app = app
        self.wallet_thread = w_thread.WalletThread(self)
        self.wallet_thread.start()
        self.server_thread = n_thread.ServerThread(self)
        self.server_thread.start()
        self._signal_handler = signal_handler.SignalHandler(self)

        # TODO
        self._signal_handler.SIGINT.connect(
            lambda: self.quit(0),
            qt_core.Qt.QueuedConnection)
        self._signal_handler.SIGQUIT.connect(
            lambda: self.quit(0),
            qt_core.Qt.QueuedConnection)
        self._signal_handler.SIGTERM.connect(
            lambda: self.quit(0),
            qt_core.Qt.QueuedConnection)

        # this way is preferrable even from the same thread
        if run_ui:
            qt_core.QMetaObject.invokeMethod(
                self,
                "run_ui",
                qt_core.Qt.QueuedConnection,
            )

    def stop_threads(self):
        self._signal_handler.close()
        self.server_thread.quit()
        self.server_thread.wait()
        self.wallet_thread.quit()
        self.wallet_thread.wait()

    @property
    def network(self) -> network.Network:
        return self.server_thread.network

    @property
    def database(self) -> database.Database:
        return self.wallet_thread.database

    def __create_settings(self):
        # !! set
        self._settings = bmnclient.config.UserConfig()
        self._settings.load()
        self.__server_version = self.get_settings(bmnclient.config.KEY_SERVER_VERSION, "")
        self.process_client_version()

    def __connect_coins(self):
        for coin in self.__all_coins:
            coin.statusChanged.connect(
                functools.partial(self._coin_status_changed, coin), qt_core.Qt.UniqueConnection)
            coin.heightChanged.connect(
                functools.partial(self.coin_height_changed, coin), qt_core.Qt.UniqueConnection)
            coin.heightChanged.connect(
                functools.partial(lambda coin: self.heightChanged.emit(coin), coin), qt_core.Qt.UniqueConnection)

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

    def coin_height_changed(self, coin: coins.CoinType):
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
            self.poll_coins()
            if self._poll_timer.short:
                log.debug("increase polling timeout")
                self._poll_timer.short = False
                self._poll_timer.start(
                    self.POLLING_SERVER_LONG_TIMEOUT, self)
        elif event.timerId() == self._mempool_timer.timerId():
            self.mempoolEveryCoin.emit()

    @property
    def wallets(self) -> List[address.CAddress]:
        return self._wallet_list

    @ property
    def first_test_address(self) -> address.CAddress:
        # why for?
        if not self.__btc_test_coin.wallets:
            raise RuntimeError("Create any btc test address")
        return self.__btc_test_coin.wallets[0]  # pylint: disable=unsubscriptable-object

    @property
    def ltc_coin(self) -> coins.CoinType:
        return self.__ltc_coin

    @property
    def btc_coin(self) -> coins.CoinType:
        return self.__btc_coin

    @property
    def all_coins(self) -> List[coins.CoinType]:
        return self.__all_coins

    @property
    def all_visible_coins(self) -> List[coins.CoinType]:
        return [c for c in self.__all_coins if c.visible and c.enabled]

    @property
    def all_enabled_coins(self) -> List[coins.CoinType]:
        return [c for c in self.__all_coins if c.enabled]

    def coin(self, name: str) -> Optional[coins.CoinType]:
        return next((c for c in self.__all_coins if c.name == name), None)

    @property
    def server_version(self) -> str:
        return self.__server_version

    @property
    def db_query_count(self) -> int:
        return self.wallet_thread.database.query_count

    @property
    def db_valid(self) -> bool:
        return self._db_valid

    @property
    def debug_man(self) -> debug_manager.DebugManager:
        return self.__debug_man

    @property
    def key_man(self) -> "KeyManager":
        return self._key_manager

    @property
    def fee_man(self) -> fee_manager.FeeManager:
        return self.__fee_manager

    @property
    def passphrase(self) -> bytes:
        return self._passphrase

    def salt(self) -> str:
        return util.hash160(self._passphrase).hex()

    @property
    def empty(self):
        return all(len(c) == 0 for c in self.__all_coins)

    @property
    def is_valid(self):
        "May be more conditions here"
        if self.__remote_server_version is None:
            return True
        return self.__server_version == self.__remote_server_version

    def process_client_version(self):
        def to_num(ver: str) -> int:
            return int("".join(ver.split('.')))
        saved_version = self.get_settings(bmnclient.config.KEY_VERSION, "")
        code_version = ".".join(map(str, e_config_version.VERSION))
        if code_version == saved_version:
            log.debug(
                f"client version is fresh: {code_version} ({to_num(saved_version)})")
            return
        elif saved_version:
            log.info(
                f"saved client version: {saved_version}. code client version: {code_version}")
            saved_num = to_num(saved_version)
            if saved_num <= 91:
                log.warning(
                    f"Old (alpha) DB version: {saved_num}. Need to erase it.")
                self._db_valid = False
                # don't save version !!!!
                return

        self.set_settings(bmnclient.config.KEY_VERSION, code_version)

    def dump_server_version(self):
        if self.__remote_server_version:
            self.__server_version = self.__remote_server_version
            self.set_settings(bmnclient.config.KEY_SERVER_VERSION, self.__server_version)
        else:
            log.warn("Local server version match with remote one")

    @ qt_core.Slot(int, str)
    def onServerVersion(self, version: int, human_version: str):
        """
        we got remote version
        if we have version in DB then test it and swear
        else just save it as actual one
        """
        log.debug(f"server version {version} / {human_version}")
        if not self.__server_version or int(version) != int(self.__server_version):
            self.__remote_server_version = version
            gui = qml_context.BackendContext.get_instance()
            if gui:
                gui.get_instance().uiManager.serverVersion = human_version
            if self.__server_version:
                log.warning("Server version mismatch !!! Local server version: %s <> Server version:%s",
                            self.__server_version, version)
            self.dump_server_version()

    def __iter__(self):
        """
        by wallets of all enabled coins
        """
        self.__coin_iter = iter(self.all_enabled_coins)
        self.__wallet_iter = iter(next(self.__coin_iter))
        return self

    def __next__(self):
        try:
            return next(self.__wallet_iter)
        except StopIteration:
            self.__wallet_iter = iter(next(self.__coin_iter))
            return next(self.__wallet_iter)

    def export_wallet(self, fpath: str):
        password = self.passphrase
        log.debug(f"Exporting wallet to {fpath} using psw:{password}")
        srl = serialization.Serializator(
            serialization.SerializationType.DEBUG
            | serialization.SerializationType.CYPHER,
            password=password)
        srl.add_one("seed", self._key_manager.master_seed_hex)
        srl.add_many("coins", iter(self.__all_coins))
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
                (c for c in self.__all_coins if c.name == coin_t["name"]), None)
            if coin is not None:
                coin.from_table(coin_t)
            else:
                log.warning(f"Coin {coin_t['name']} isn't found")
        self.save_coins_with_addresses()
        qml_context.BackendContext.get_instance().coinManager.update_coin_model()

    def reset_wallet(self):
        self.dropDb.emit()
        self.remove_password()
        self.__server_version = None
        for c in self.__all_coins:
            c.clear()

    def __getitem__(self, val: Union[int, str]):
        if isinstance(val, str):
            return next((c for c in self.all_coins if c.name == val), None)
        return self.all_visible_coins[val]

    def __len__(self) -> int:
        return len(self.all_visible_coins)

    def get_settings(self, name, default, value_type=str) -> Any:
        return self._settings.get(name, value_type, default)

    def set_settings(self, name: str, value: Any) -> None:
        self._settings.set(name, value)

    @ property
    def post_count(self) -> int:
        return self.__post_count

    @ post_count.setter
    def post_count(self, val: int) -> None:
        with self.__post_mutex:
            self.__post_count = val
