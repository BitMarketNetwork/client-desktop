# JOK++
from __future__ import annotations

from typing import Callable, Optional

from .coin import AbstractCoin
from ..utils.static_list import StaticList
from ..wallet import coins


class CoinList(StaticList):
    ItemType = AbstractCoin

    def __init__(
            self,
            *,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        super().__init__(
            (
                coins.Bitcoin(model_factory=model_factory),
                coins.BitcoinTest(model_factory=model_factory),
                coins.Litecoin(model_factory=model_factory)
            ),
            item_property="shortName"
        )
