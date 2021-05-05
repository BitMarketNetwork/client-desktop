from __future__ import annotations

import itertools
import logging
from typing import Iterable, Optional, Union

import PySide2.QtCore as qt_core

from . import address, coin_network, hd, key
from ..utils.meta import classproperty
from ..coins import coin_bitcoin
from ..coins import coin_litecoin
from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class CoinType(qt_core.QObject):
    name: str = None

    network: coin_network.CoinNetworkBase = None
    visibleChanged = qt_core.Signal()

    @classproperty
    def all(cls) -> Iterable:  # pylint: disable=E0213
        return (val for _, val in globals().items() if isinstance(val, type) and issubclass(val, cls) and val is not cls)

    def __init__(self):
        super().__init__()
        self.__visible = True

    def add_watch_address(self, name: str, label: str = "") -> AbstractCoin.Address:
        adr = AbstractCoin.Address(
            self,
            name=name,
            label=label)
        self.appendAddress(adr)
        from ..application import CoreApplication
        CoreApplication.instance().databaseThread.save_address(adr)
        return adr

    @property
    def private_key(self) -> key.PrivateKey:
        if self.__hd_node:
            return self.__hd_node.key

    @property
    def tx_count(self) -> int:
        return sum(len(w) for w in self._address_list)

    def empty(self, skip_zero: bool) -> bool:
        if skip_zero:
            return next((w for w in self._address_list if self._amount != 0), None) is None
        return not self

    def __iter__(self) -> "CoinType":
        self.__wallet_iter = iter(self._address_list)
        return self

    def __next__(self) -> AbstractCoin.Address:
        return next(self.__wallet_iter)

    # abc implemented it but we can do it better
    def __contains__(self, value: Union[str, AbstractCoin.Address]) -> bool:
        if not isinstance(value, str):
            value = value.name
        return any(value == add.name for add in self._address_list)

    def __len__(self) -> int:
        return len(self._address_list)

    def __bool__(self) -> bool:
        return bool(self._address_list)

    # don't bind not_empty with addressModel !!! . beware recursion
    def __getitem__(self, key: Union[int, str]) -> AbstractCoin.Address:
        if isinstance(key, int):
            return self._address_list[key]
        if isinstance(key, str):
            return next((w for w in self._address_list if w.name == key), None)

    @qt_core.Property(bool, notify=visibleChanged)
    def visible(self) -> bool:
        return self.__visible

    @visible.setter
    def _set_visible(self, ex: bool):
        if ex != self.__visible:
            self.__visible = ex
            self.visibleChanged.emit()
            self._state_model.refresh()


class Bitcoin(CoinType, coin_bitcoin.Bitcoin):
    name = "btc"
    network = coin_network.BitcoinMainNetwork

    def __init__(self, **kwargs) -> None:
        super().__init__()
        coin_bitcoin.Bitcoin.__init__(self, **kwargs)


class BitcoinTest(Bitcoin, coin_bitcoin.BitcoinTest):
    name = "btctest"
    network = coin_network.BitcoinTestNetwork


class Litecoin(CoinType, coin_litecoin.Litecoin):
    name = "ltc"
    network = coin_network.LitecoinMainNetwork

    def __init__(self, **kwargs) -> None:
        super().__init__()
        coin_litecoin.Litecoin.__init__(self, **kwargs)
