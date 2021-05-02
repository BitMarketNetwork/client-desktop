from __future__ import annotations

import itertools
import logging
from typing import Iterable, Optional, Union

import PySide2.QtCore as qt_core

from . import address, coin_network, hd, key
from ..utils.meta import classproperty
from ..coins import coin_bitcoin
from ..coins import coin_litecoin

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

    def _next_hd_index(self):
        idxs = [a.hd_index for a in self._address_list]
        return next(k for k in itertools.count(1) if k not in idxs)

    def make_address(self, type_: key.AddressType = key.AddressType.P2WPKH, label: str = "", message: str = "") -> address.CAddress:
        if self._hd_path is None:
            raise address.AddressError(f"There's no private key in {self}")
        hd_index = 1
        while any(w.hd_index == hd_index for w in self._address_list):
            hd_index += 1
        new_hd = self._hd_path.make_child_prv(
            self._next_hd_index(),
            False,
            self.network)
        wallet = address.CAddress.make_from_hd(new_hd, self, type_)
        assert wallet.hd_index == hd_index
        wallet.label = label
        wallet._message = message
        self.appendAddress(wallet)
        from ..application import CoreApplication
        CoreApplication.instance().databaseThread.save_address(wallet)
        return wallet

    def add_watch_address(self, name: str, label: str = "") -> address.CAddress:
        adr = address.CAddress(
            self,
            name=name,
            label=label)
        adr.create()
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

    def __next__(self) -> address.CAddress:
        return next(self.__wallet_iter)

    # abc implemented it but we can do it better
    def __contains__(self, value: Union[str, address.CAddress]) -> bool:
        if not isinstance(value, str):
            value = value.name
        return any(value == add.name for add in self._address_list)

    def __len__(self) -> int:
        return len(self._address_list)

    def __bool__(self) -> bool:
        return bool(self._address_list)

    # don't bind not_empty with addressModel !!! . beware recursion
    def __getitem__(self, key: Union[int, str]) -> address.CAddress:
        if isinstance(key, int):
            return self._address_list[key]
        if isinstance(key, str):
            return next((w for w in self._address_list if w.name == key), None)

    def _update_wallets(
            self,
            from_=Optional[int],
            remove_txs_from: Optional[int] = None,
            verbose: bool = False):
        "from old to new one !!!"
        for w in self._address_list:
            w.update_tx_list(from_, remove_txs_from, verbose)

    def clear(self):
        for addr in self._address_list:
            addr.clear()
        self._address_list.clear()
        self.refreshAmount()  # TODO

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
