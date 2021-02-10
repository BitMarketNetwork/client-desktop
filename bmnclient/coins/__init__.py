from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Type

from .address import AddressBase

if TYPE_CHECKING:
    from ..language import Locale


class CoinBase:
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _UNIT = ""
    _DECIMAL_SIZE = 0

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

    @property
    def decimalValue(self) -> int:
        return 10 ** self._DECIMAL_SIZE

    @classmethod
    def isValidAmount(cls, amount: int) -> bool:
        # limit to int64
        return -(2 ** 63) <= amount <= (2 ** 63 - 1)

    def stringToAmount(
            self,
            source: str,
            *,
            locale: Optional[Locale] = None) -> Optional[int]:
        if not source:
            return None

        sign = False
        if (
                source[0] == "-" or
                (locale and source[0] == locale.negativeSign())
        ):
            sign = True
            source = source[1:]
        elif (
                source[0] == "+" or
                (locale and source[0] == locale.positiveSign())
        ):
            source = source[1:]

        a = source.rsplit(locale.decimalPoint() if locale else ".")
        if len(a) == 1:
            b = ""
            a = a[0]
        elif len(a) == 2:
            b = a[1]
            a = a[0]
        else:
            return None
        if not a and not b:
            return None

        result = 0
        if a:
            if locale:
                a = locale.stringToInteger(a)
            elif a.isalnum():
                try:
                    a = int(a, base=10)
                except ValueError:
                    a = None
            else:
                a = None
            if a is None or a < 0:
                return None
            result = (-a if sign else a) * self.decimalValue

        if b:
            b_length = len(b)
            if b_length > self._DECIMAL_SIZE:
                return None
            if b.isalnum():
                try:
                    b = int(b, base=10)
                except ValueError:
                    b = None
            else:
                b = None
            if b is None or b < 0 or b >= self.decimalValue:
                return None
            for _ in range(b_length, self._DECIMAL_SIZE):
                b *= 10
            result += (-b if sign else b)

        if not self.isValidAmount(result):
            return None
        return result

    def amountToString(
            self,
            amount: int,
            *,
            locale: Optional[Locale] = None) -> str:
        if not amount or not self.isValidAmount(amount):
            return "0"
        if amount < 0:
            amount = abs(amount)
            result = locale.negativeSign() if locale else "-"
        else:
            result = ""

        a, b = divmod(amount, self.decimalValue)

        zero_count = 0
        while b and b % 10 == 0:
            b //= 10
            zero_count += 1

        result += locale.integerToString(a) if locale else str(a)
        if b:
            b = str(b)
            zero_count = self._DECIMAL_SIZE - len(b) - zero_count
            result += locale.decimalPoint() if locale else "."
            result += ("0" * zero_count) + str(b)

        return result


class Bitcoin(CoinBase):
    from .address import BitcoinAddress
    _SHORT_NAME = "btc"
    _FULL_NAME = "Bitcoin"
    _UNIT = "BTC"
    _DECIMAL_SIZE = 8

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
