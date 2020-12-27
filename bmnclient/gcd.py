import datetime
import functools
import logging
import threading
from typing import Any, List, Optional, Union

import PySide2.QtCore as qt_core

import bmnclient.config
import bmnclient.config
import bmnclient.version
from bmnclient import version as e_config_version
from . import loading_level, debug_manager, signal_handler, meta
from .server import network, thread as n_thread
from .ui.gui import qml_context
from .wallet import aes, mutable_tx, tx, address, coins, \
    fee_manager, serialization, thread as w_thread, util
from .wallet.database import database
from bmnclient.ui import CoreApplication
log = logging.getLogger(__name__)


class GcdError(Exception):
    pass


class GCD(meta.QSeq):
    POLLING_SERVER_LONG_TIMEOUT = 10000
    POLLING_SERVER_SHORT_TIMEOUT = 3000
    MEMPOOL_MONITOR_TIMEOUT = 60000

    saveCoin = qt_core.Signal(coins.CoinType, arguments=["coin"])
    lookForHDChain = qt_core.Signal(coins.CoinType, arguments=["coin"])
    saveAddress = qt_core.Signal(
        address.CAddress, int, arguments=["wallet", "timeout"])
    updateAddress = qt_core.Signal(address.CAddress, arguments=["wallet"])
    validateAddress = qt_core.Signal(
        coins.CoinType, str, arguments=["coin,address"])
    mempoolCoin = qt_core.Signal(coins.CoinType, arguments=["coin"])
    mempoolEveryCoin = qt_core.Signal()
    startNetwork = qt_core.Signal()
    updateTxStatus = qt_core.Signal(tx.Transaction)
    fakeMempoolSearch = qt_core.Signal(tx.Transaction)
    heightChanged = qt_core.Signal(coins.CoinType, arguments=["coin"])
    eraseWallet = qt_core.Signal(address.CAddress, arguments=["wallet"])
    clearAddressTx = qt_core.Signal(address.CAddress, arguments=["address"])
    removeTxList = qt_core.Signal(list)
    undoTx = qt_core.Signal(coins.CoinType, int)
    httpFailureSimulation = qt_core.Signal(int)
    unspentsOfWallet = qt_core.Signal(address.CAddress, arguments=["wallet"])
    debugUpdateHistory = qt_core.Signal(address.CAddress, arguments=["wallet"])
    retrieveCoinHistory = qt_core.Signal(coins.CoinType, arguments=["coin"])
    netError = qt_core.Signal(int, str, arguments=["code,error"])
    dropDb = qt_core.Signal()
    resetDb = qt_core.Signal(bytes, arguments=["password"])
    broadcastMtx = qt_core.Signal(
        mutable_tx.MutableTransaction, arguments=["mtx"])
    saveTx = qt_core.Signal(tx.Transaction, arguments=["tx"])
    saveTxList = qt_core.Signal(address.CAddress, list)
    dbLoaded = qt_core.Signal(int)
    # TODO: connect it
    # updateTxs = qt_core.Signal(address.CAddress, arguments=["wallet"])
    addressHistory = qt_core.Signal( address.CAddress )
    saveMeta = qt_core.Signal(str, str, arguments=["name", "value"])
    applyPassword = qt_core.Signal(
        bytes, bytes, arguments=["password", "nonce"])

    def __init__(self, silent_mode: bool = False, parent=None):
        assert isinstance(silent_mode, bool)
        self.__class__.__instance = self

        super().__init__(parent=parent)

        self.launch_time = datetime.datetime.utcnow()
        self.silent_mode = silent_mode
        self._mempool_timer = qt_core.QBasicTimer()
        self._poll_timer = qt_core.QBasicTimer()
        self.__debug_man = debug_manager.DebugManager(self)
        from bmnclient.wallet import master_key
        self._key_manager = master_key.KeyManager(self)
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
        self.__post_count = 0
        self.__post_mutex = threading.Lock()
        self._mnemo: bytes = None
        self._db_valid = True

        user_config = CoreApplication.instance().userConfig
        self.__server_version = user_config.get(
            bmnclient.config.UserConfig.KEY_SERVER_VERSION,
            str,
            "")
        self.process_client_version()

        for coin in self.__all_coins:
            coin.statusChanged.connect(
                functools.partial(self._coin_status_changed, coin), qt_core.Qt.UniqueConnection)
            coin.heightChanged.connect(
                functools.partial(self.coin_height_changed, coin), qt_core.Qt.UniqueConnection)
            coin.heightChanged.connect(
                functools.partial(lambda coin: self.heightChanged.emit(coin), coin), qt_core.Qt.UniqueConnection)

    def start_threads(self):
        self.wallet_thread = w_thread.WalletThread(self)
        self.wallet_thread.start()
        self.server_thread = n_thread.ServerThread(self)
        self.server_thread.start()

    @property
    def network(self) -> network.Network:
        return self.server_thread.network

    @property
    def database(self) -> database.Database:
        return self.wallet_thread.database

    def save_coins(self):
        qt_core.QMetaObject.invokeMethod(self.wallet_thread.database,"save_coins",qt_core.Qt.QueuedConnection,)

    def save_coins_with_addresses(self):
        qt_core.QMetaObject.invokeMethod(self.wallet_thread.database,"save_coins_with_addresses",qt_core.Qt.QueuedConnection,)

    def save_coins_settings(self):
        qt_core.QMetaObject.invokeMethod(self.wallet_thread.database,"save_coins_settings",qt_core.Qt.QueuedConnection,)

    def retrieve_fee(self):
        qt_core.QMetaObject.invokeMethod(self.network, "retrieve_fee",qt_core.Qt.QueuedConnection,)

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
    def empty(self):
        return all(len(c) == 0 for c in self.__all_coins)

    def process_client_version(self):
        def to_num(ver: str) -> int:
            return int("".join(ver.split('.')))
        user_config = CoreApplication.instance().userConfig
        saved_version = user_config.get(
            bmnclient.config.UserConfig.KEY_VERSION,
            str,
            "")
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

        user_config = CoreApplication.instance().userConfig
        user_config.set(bmnclient.config.UserConfig.KEY_VERSION, code_version)

    def dump_server_version(self):
        if self.__remote_server_version:
            self.__server_version = self.__remote_server_version
            user_config = CoreApplication.instance().userConfig
            user_config.set(bmnclient.config.UserConfig.KEY_SERVER_VERSION, self.__server_version)
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
        password = self._passphrase
        log.debug(f"Exporting wallet to {fpath} using psw:{password}")
        srl = serialization.Serializator(
            serialization.SerializationType.DEBUG
            | serialization.SerializationType.CYPHER,
            password=password)
        srl.add_one("seed", self._key_manager.master_seed_hex)
        srl.add_many("coins", iter(self.__all_coins))
        srl.to_file(fpath)

    def import_wallet(self, fpath: str):
        password = self._passphrase
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
        self.reset_db()
        self.__server_version = None
        for c in self.__all_coins:
            c.clear()

    def __getitem__(self, val: Union[int, str]):
        if isinstance(val, str):
            return next((c for c in self.all_coins if c.name == val), None)
        return self.all_visible_coins[val]

    def __len__(self) -> int:
        return len(self.all_visible_coins)

    @ property
    def post_count(self) -> int:
        return self.__post_count

    @ post_count.setter
    def post_count(self, val: int) -> None:
        with self.__post_mutex:
            self.__post_count = val

    @classmethod
    def get_instance(cls):
        # take care of the test ( test_tr )
        return getattr(cls, "_GCD__instance", None)
        # return cls.__instance

    def add_address(self, address: str, coin_str: str = None, coin: coins.CoinType = None):
        if coin is None:
            coin = next((c for c in self.all_coins if c.match(coin_str)), None)
            if coin is None:
                raise GcdError(
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
        qt_core.QMetaObject.invokeMethod(self.network,"poll_coins",qt_core.Qt.QueuedConnection)
        #  self.network.poll_coins()

    def save_meta(self, key: str, value: str):
        self.saveMeta.emit(key, value)

    @qt_core.Slot(address.CAddress)
    def update_wallet(self, wallet):
        """
        don't be confused with poll_coins !!! they have different meaning !
        """
        if not self.silent_mode:
            self.updateAddress.emit(wallet)

    def update_wallets(self, coin: Optional[coins.CoinType] = None):
        if coin is None:
            coin = self
        for addr in coin:
            self.update_wallet(addr)

    def select_wallet(self, pref: str):
        return next(w for w in self if w.match(pref))

    def release(self):
        self.stop_poll()
        qt_core.QMetaObject.invokeMethod(self.network, "abort",qt_core.Qt.QueuedConnection,)
        qt_core.QMetaObject.invokeMethod(self.database,"abort",qt_core.Qt.QueuedConnection,)

        self.server_thread.quit()
        self.server_thread.wait()
        self.wallet_thread.quit()
        self.wallet_thread.wait()

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

    def process_all_txs(self):
        for w in self:
            for tx_ in w.txs:
                tx_.process()

    def unspent_list(self, address):
        if address.wants_update_unspents:
            self.unspentsOfWallet.emit(address)

    def save_master_seed(self, seed):
        self.saveMeta.emit("seed", seed)

    def save_mnemo(self, mnemo: str):
        # test case
        if self._passphrase is None:
            log.critical("NO PASSPHRASE")
            return
        # we can't use DB for mnemo ! 'cause user can reset DB but leave master key
        self._mnemo = aes.AesProvider(self._passphrase).encode(
            util.get_bytes(mnemo), True)
        # log.debug(f"mnemo {self._mnemo} saved")
        user_config = CoreApplication.instance().userConfig
        user_config.set(
            bmnclient.config.UserConfig.KEY_WALLET_SEED,
            self._mnemo.hex())

    def get_mnemo(self, password: Optional[str] = None) -> str:
        if self._mnemo is None:
            user_config = CoreApplication.instance().userConfig
            self._mnemo = user_config.get(
                bmnclient.config.UserConfig.KEY_WALLET_SEED,
                str,
                "").fromhex()
        if self._mnemo:
            if password is None:
                try:
                    return aes.AesProvider(self._passphrase).decode(self._mnemo, True).decode()
                except aes.AesError as ae:
                    log.warning(f"AES error: {ae}")
            else:
                der = key_derivation.KeyDerivation(password)
                user_config = CoreApplication.instance().userConfig

                if der.check(bytes.fromhex(
                        user_config.get(bmnclient.config.UserConfig.KEY_WALLET_SECRET, str, "ff"))):
                    try:
                        return aes.AesProvider(der.value()).decode(self._mnemo, True).decode()
                    except aes.AesError as ae:
                        log.warning(f"AES error: {ae}")
        # log.warning(f"mnemo: {self._mnemo}")

    def on_meta(self, key: str, value: str):
        log.debug(f"meta value read: {key}:")
        if key == "seed":
            if value:
                self._key_manager.apply_master_seed(
                    util.hex_to_bytes(value), save=False)
                self.look_for_HD()
            else:
                log.debug(f"No master then request it")
                self._key_manager.mnemoRequested.emit()
        else:
            log.error(f"Unknown meta key read: {key}")

    def clear_transactions(self, address):
        self.clearAddressTx.emit(address)
        address.clear()
        # to save offsetts
        self.saveAddress.emit(address, None)

    def apply_password(self, password) -> None:
        self.applyPassword.emit(password, b"123")
        if not self.silent_mode:
            self._poll_timer.short = True
            self._poll_timer.start(self.POLLING_SERVER_SHORT_TIMEOUT, self)
            self._mempool_timer.start(self.MEMPOOL_MONITOR_TIMEOUT, self)

    def reset_db(self) -> None:
        self.dropDb.emit()
        user_config = CoreApplication.instance().userConfig
        user_config.set(bmnclient.config.UserConfig.KEY_VERSION, e_config_version.VERSION)
        self._db_valid = True

    def look_for_HD(self):
        for coin in self.all_enabled_coins:
            log.debug(f"Looking for HD chain: {coin}")
            self.lookForHDChain.emit(coin)

    def validate_address(self, coin_index: int, address: str) -> None:
        coin = self[coin_index]
        self.validateAddress.emit(coin, address)

    def save_tx_list(self, address, tx_list):
        self.saveTxList.emit(address, tx_list)
        self.post_count += 1

    def db_level_loaded(self, level: int) -> None:
        "not gui !!!"
        self.dbLoaded.emit(level)
        if level == loading_level.LoadingLevel.ADDRESSES:
            qml_context.BackendContext.get_instance().coinManager.update_coin_model()

    def update_coin(self, index: int) -> None:
        self.poll_coins()

    def clear_coin(self, index: int) -> None:
        for add in self[index]:
            self.delete_wallet(add)
        self[index].clear()
