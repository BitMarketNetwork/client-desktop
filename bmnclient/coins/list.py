# JOK++
from __future__ import annotations

from collections.abc import Sequence
from typing import Callable, Iterator, Optional, Union

from ..wallet import coins


class CoinList(Sequence):
    def __init__(
            self,
            *,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        self._list = (
            coins.Bitcoin(model_factory=model_factory),
            coins.BitcoinTest(model_factory=model_factory),
            coins.Litecoin(model_factory=model_factory)
        )

    def __iter__(self) -> Iterator[coins.CoinType]:
        return iter(self._list)

    def __len__(self) -> int:
        return len(self._list)

    def __getitem__(self, name: Union[str, int]) -> Optional[coins.CoinType]:
        if isinstance(name, str):
            for coin in self._list:
                if coin.name == name:
                    return coin
        elif 0 <= name <= len(self._list):
            return self._list[name]
        return None
