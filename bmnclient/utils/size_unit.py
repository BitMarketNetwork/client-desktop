from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

from enum import Enum


class SizeUnitConverter:
    @staticmethod
    def sizeToUnit(value: int, unit: Enum) -> Optional[int]:
        try:
            if unit == SizeUnit.KB:
                return int(value / 1024)
            elif unit == SizeUnit.MB:
                return int(value / (1024 * 1024))
            elif unit == SizeUnit.GB:
                return int(value / (1024 * 1024 * 1024))
            elif unit == SizeUnit.TB:
                return int(value / (1024 * 1024 * 1024 * 1024))
            else:
                return value
        except OverflowError:
            return None

    @staticmethod
    def unitToSize(value: int, unit: Enum) -> Optional[int]:
        try:
            if unit == SizeUnit.KB:
                return value * 1024
            elif unit == SizeUnit.MB:
                return value * (1024 * 1024)
            elif unit == SizeUnit.GB:
                return value * (1024 * 1024 * 1024)
            elif unit == SizeUnit.TB:
                return value * (1024 * 1024 * 1024 * 1024)
            else:
                return value
        except OverflowError:
            return None


class SizeUnit(Enum):
    B = 1
    KB = 2
    MB = 3
    GB = 4
    TB = 5
