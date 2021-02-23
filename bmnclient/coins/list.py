# JOK++
from __future__ import annotations

from collections.abc import Sequence
from typing import Iterator, Optional, Type, Union

from ..wallet import coins


class CoinList(Sequence):
    def __init__(self, model: Type, **kwargs) -> None:
        self._list = (
            type("Bitcoin", (model, coins.Bitcoin), {})(**kwargs),
            type("BitcoinTest", (model, coins.BitcoinTest), {})(**kwargs),
            type("Litecoin", (model, coins.Litecoin), {})(**kwargs),
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
