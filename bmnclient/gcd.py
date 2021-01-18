import functools
import logging
from typing import List, Optional, Union
import PySide2.QtCore as qt_core
from . import meta
from .wallet import address, coins
log = logging.getLogger(__name__)


class GCD(meta.QSeq):
    def __init__(self, application):
        super().__init__()

        self.__all_coins = [
            coins.Bitcoin(self),
            coins.BitcoinTest(self),
            coins.Litecoin(self),
        ]

        for coin in self.__all_coins:
            application.networkThread.heightChanged.connect(
                functools.partial(self.coin_height_changed, coin),
                qt_core.Qt.UniqueConnection)
            application.networkThread.heightChanged.connect(
                functools.partial(lambda coin: application.networkThread.heightChanged.emit(coin), coin),
                qt_core.Qt.UniqueConnection)

    def coin_height_changed(self, coin: coins.CoinType):
        # log.info(f"Coin height changed for {coin} to {coin.height}")
        from .application import CoreApplication
        CoreApplication.instance().networkThread.retrieveCoinHistory.emit(coin)

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

    def __getitem__(self, val: Union[int, str]):
        if isinstance(val, str):
            return next((c for c in self.all_coins if c.name == val), None)
        return self.all_visible_coins[val]

    def __len__(self) -> int:
        return len(self.all_visible_coins)
