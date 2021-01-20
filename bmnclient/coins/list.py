from __future__ import annotations
from ..wallet import coins
from typing import Iterator, Union, Optional


class CoinList:
    def __init__(self) -> None:
        self._list = (
            coins.Bitcoin(None),
            coins.BitcoinTest(None),
            coins.Litecoin(None),
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
