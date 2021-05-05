# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils.static_list import StaticList
from ..wallet import coins

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
                coins.Bitcoin(model_factory=model_factory),
                coins.BitcoinTest(model_factory=model_factory),
                coins.Litecoin(model_factory=model_factory)
            ),
            item_property="shortName"
        )

    def __iter__(self) -> Iterator[AbstractCoin]:
        return super().__iter__()

    def __getitem__(self, value: Union[str, int]) -> Optional[AbstractCoin]:
        return super().__getitem__(value)
