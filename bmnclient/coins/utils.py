# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional, Union
    from .abstract.coin import AbstractCoin


class CoinLoggerUtils(NotImplementedInstance):
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
    def txToNameSuffix(cls, tx: AbstractCoin.Tx):
        return "{}:{}".format(tx.coin.name, tx.name)

    @classmethod
    def nameToSubSuffix(cls, key: str, value: Union[str, int]) -> str:
        if key:
            return ":{}={}".format(key, value)
        return ":{}".format(value)
