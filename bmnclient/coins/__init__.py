from __future__ import annotations


class CoinBase:
    _SHORT_NAME = ""
    _FULL_NAME = ""

    @property
    def shortName(self) -> str:
        return self._SHORT_NAME

    @property
    def fullName(self) -> str:
        return self._FULL_NAME

    def stringToAmount(self, source: str) -> int:
        raise NotImplementedError

    def amountToString(self, amount: int) -> str:
        raise NotImplementedError


class Bitcoin(CoinBase):
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"


class BitcoinTest(Bitcoin):
    _SHORT_NAME = "btctest"
    _FULL_NAME = "Bitcoin Testnet"


class Litecoin(Bitcoin):
    _SHORT_NAME = "ltc"
    _FULL_NAME = "Litecoin"
