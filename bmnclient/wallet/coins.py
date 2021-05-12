from __future__ import annotations

from typing import Union

import PySide2.QtCore as qt_core

from . import coin_network
from ..coins import coin_bitcoin, coin_litecoin
from ..coins.abstract.coin import AbstractCoin


class CoinType(qt_core.QObject):
    network: coin_network.CoinNetworkBase = None

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


class Bitcoin(CoinType, coin_bitcoin.Bitcoin):
    network = coin_network.BitcoinMainNetwork

    def __init__(self, **kwargs) -> None:
        super().__init__()
        coin_bitcoin.Bitcoin.__init__(self, **kwargs)


class BitcoinTest(Bitcoin, coin_bitcoin.BitcoinTest):
    network = coin_network.BitcoinTestNetwork


class Litecoin(CoinType, coin_litecoin.Litecoin):
    network = coin_network.LitecoinMainNetwork

    def __init__(self, **kwargs) -> None:
        super().__init__()
        coin_litecoin.Litecoin.__init__(self, **kwargs)
