# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .coin_bitcoin import Bitcoin, BitcoinTest
from .coin_litecoin import Litecoin
from ..utils.static_list import StaticList

if TYPE_CHECKING:
    from typing import Callable, Iterator, Optional, Union
    from .abstract.coin import AbstractCoin


class CoinList(StaticList):
    def __init__(
            self,
            *,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        super().__init__(
            (
                Bitcoin(model_factory=model_factory),
                BitcoinTest(model_factory=model_factory),
                Litecoin(model_factory=model_factory)
            ),
            item_property="name"
        )

    def __iter__(self) -> Iterator[AbstractCoin]:
        return super().__iter__()

    def __getitem__(self, value: Union[str, int]) -> Optional[AbstractCoin]:
        return super().__getitem__(value)
