# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Union
    from .abstract.coin import AbstractCoin


class LoggerUtils:
    @classmethod
    def coinToNameSuffix(cls, coin: AbstractCoin):
        return coin.name

    @classmethod
    def addressToNameSuffix(
            cls,
            address: AbstractCoin.Address,
            hd_index: Optional[int] = None):
        value = "{}:{}".format(address.coin.name, address.name)
        if hd_index is not None:
            value += cls.nameToSubSuffix("hd_index", hd_index)
        return value

    @classmethod
    def nameToSubSuffix(cls, key: str, value: Union[str, int]) -> str:
        if key:
            return ":{}={}".format(key, value)
        return ":{}".format(value)
