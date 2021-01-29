from __future__ import annotations

from .address import AddressBase

from typing import Type


class CoinBase:
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _UNIT = ""

    @property
    def shortName(self) -> str:
        return self._SHORT_NAME

    @property
    def fullName(self) -> str:
        return self._FULL_NAME

    def unit(self) -> str:
        return self._UNIT

    @property
    def iconPath(self) -> str:
        # relative to "resources/images"
        return "coins/" + self._SHORT_NAME + ".svg"

    @property
    def address(self) -> Type[AddressBase]:
        raise NotImplementedError

    def stringToAmount(self, source: str) -> int:
        raise NotImplementedError

    def amountToString(self, amount: int) -> str:
        raise NotImplementedError


class Bitcoin(CoinBase):
    from .address import BitcoinAddress
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"
    _UNIT = "BTC"

    @property
    def address(self) -> Type[BitcoinAddress]:
        return self.BitcoinAddress


class BitcoinTest(Bitcoin):
    from .address import BitcoinTestAddress
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"
    _UNIT = "BTC"

    @property
    def address(self) -> Type[BitcoinTestAddress]:
        return self.BitcoinTestAddress


class Litecoin(Bitcoin):
    from .address import LitecoinAddress
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"
    _UNIT = "LTC"

    @property
    def address(self) -> Type[LitecoinAddress]:
        return self.LitecoinAddress
