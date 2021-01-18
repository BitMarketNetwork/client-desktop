import datetime
import functools
import logging
from typing import List, Optional, Union
import PySide2.QtCore as qt_core
from . import debug_manager, meta
from .wallet import address, coins, fee_manager, serialization, util
from .application import CoreApplication
log = logging.getLogger(__name__)


class GcdError(Exception):
    pass


class GCD(meta.QSeq):
    def __init__(self):
        super().__init__()

        self.launch_time = datetime.datetime.utcnow()
        self.__debug_man = debug_manager.DebugManager(self)
        self.__fee_manager = fee_manager.FeeManager(self)

        self.__all_coins = [
            coins.Bitcoin(self),
            coins.BitcoinTest(self),
            coins.Litecoin(self),
        ]

        for coin in self.__all_coins:
            coin.statusChanged.connect(
                functools.partial(self._coin_status_changed, coin), qt_core.Qt.UniqueConnection)
            coin.heightChanged.connect(
                functools.partial(self.coin_height_changed, coin), qt_core.Qt.UniqueConnection)
            coin.heightChanged.connect(
                functools.partial(lambda coin: self.heightChanged.emit(coin), coin), qt_core.Qt.UniqueConnection)

    def _coin_status_changed(self, coin: coins.CoinType):
        log.debug(F"Coin status changed for {coin}")
        # TODO:

    def coin_height_changed(self, coin: coins.CoinType):
        # log.info(f"Coin height changed for {coin} to {coin.height}")
        self.retrieveCoinHistory.emit(coin)

    @property
    def wallets(self) -> List[address.CAddress]:
        return self._wallet_list

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
    def debug_man(self) -> debug_manager.DebugManager:
        return self.__debug_man

    @property
    def fee_man(self) -> fee_manager.FeeManager:
        return self.__fee_manager

    @property
    def empty(self):
        return all(len(c) == 0 for c in self.__all_coins)

    @qt_core.Slot(int, str)
    def onServerVersion(self, version: int, human_version: str):
        log.debug(f"server version {version} / {human_version}")
        from .ui.gui import Application
        Application.instance().uiManager.serverVersion = human_version

    def __iter__(self):
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
        password = self._passphrase  # TODO
        log.debug(f"Exporting wallet to {fpath} using psw:{password}")
        srl = serialization.Serializator(
            serialization.SerializationType.DEBUG
            | serialization.SerializationType.CYPHER,
            password=password)
        # TODO srl.add_one("seed", CoreApplication.instance().keyStore.master_seed_hex)
        srl.add_many("coins", iter(self.__all_coins))
        srl.to_file(fpath)

    def import_wallet(self, fpath: str):
        password = self._passphrase  # TODO
        log.debug(f"Importing wallet from {fpath} using psw:{password}")
        dsrl = serialization.DeSerializator(fpath, password=password)
        # need to cleanup old stuff
        self.resetDb.emit(self._passphrase)  # TODO
        CoreApplication.instance().keyStore.apply_master_seed(
            util.hex_to_bytes(dsrl["seed"]))
        for coin_t in dsrl["coins"]:
            coin = next(
                (c for c in self.__all_coins if c.name == coin_t["name"]), None)
            if coin is not None:
                coin.from_table(coin_t)
            else:
                log.warning(f"Coin {coin_t['name']} isn't found")
        CoreApplication.instance().databaseThread.save_coins_with_addresses()
        from .ui.gui import Application
        Application.instance().coinManager.update_coin_model()

    def reset_wallet(self):
        CoreApplication.instance().databaseThread.reset_db()
        for c in self.__all_coins:
            c.clear()

    def __getitem__(self, val: Union[int, str]):
        if isinstance(val, str):
            return next((c for c in self.all_coins if c.name == val), None)
        return self.all_visible_coins[val]

    def __len__(self) -> int:
        return len(self.all_visible_coins)
