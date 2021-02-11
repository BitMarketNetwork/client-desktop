from __future__ import annotations

from functools import lru_cache
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..language import Locale


class AbstractCurrency:
    _DECIMAL_SIZE = 0
    _VALUE_BITS = 63  # int64
    _UNIT = "YYY"

    def __init__(self) -> None:
        raise TypeError

    @classmethod
    def isValidValue(cls, value: int) -> bool:
        b = 2 ** cls._VALUE_BITS
        return -b <= value <= (b - 1)

    @classmethod
    @lru_cache
    def stringTemplate(cls) -> str:
        v = len(cls.toString(2 ** cls._VALUE_BITS - 1))
        assert v > 2
        return "8" * (1 + v + v // 3)

    @classmethod
    def fromString(
            cls,
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
            result = (-a if sign else a) * (10 ** cls._DECIMAL_SIZE)

        if b:
            b_length = len(b)
            if b_length > cls._DECIMAL_SIZE:
                return None
            if b.isalnum():
                try:
                    b = int(b, base=10)
                except ValueError:
                    b = None
            else:
                b = None
            if b is None or b < 0 or b >= (10 ** cls._DECIMAL_SIZE):
                return None
            for _ in range(b_length, cls._DECIMAL_SIZE):
                b *= 10
            result += (-b if sign else b)

        if not cls.isValidValue(result):
            return None
        return result

    @classmethod
    def toString(
            cls,
            value: int,
            *,
            locale: Optional[Locale] = None) -> str:
        if not value or not cls.isValidValue(value):
            return "0"
        if value < 0:
            value = abs(value)
            result = locale.negativeSign() if locale else "-"
        else:
            result = ""

        a, b = divmod(value, (10 ** cls._DECIMAL_SIZE))

        zero_count = 0
        while b and b % 10 == 0:
            b //= 10
            zero_count += 1

        result += locale.integerToString(a) if locale else str(a)
        if b:
            b = str(b)
            zero_count = cls._DECIMAL_SIZE - len(b) - zero_count
            result += locale.decimalPoint() if locale else "."
            result += ("0" * zero_count) + str(b)

        return result
