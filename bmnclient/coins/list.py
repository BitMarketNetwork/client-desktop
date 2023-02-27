from __future__ import annotations

from typing import TYPE_CHECKING

from .coin_bitcoin import Bitcoin, BitcoinTest
from .coin_litecoin import Litecoin
from ..utils import StaticList

if TYPE_CHECKING:
    from typing import Iterator, Optional, Union
    from .abstract import Coin, CoinModelFactory


class CoinList(StaticList):
    def __init__(self, *, model_factory: CoinModelFactory) -> None:
        super().__init__(
            (
                Bitcoin(model_factory=model_factory),
                BitcoinTest(model_factory=model_factory),
                Litecoin(model_factory=model_factory),
            ),
            item_property="name"
        )

    def __iter__(self) -> Iterator[Coin]:
        return super().__iter__()

    def __getitem__(self, value: Union[str, int]) -> Optional[Coin]:
        return super().__getitem__(value)
