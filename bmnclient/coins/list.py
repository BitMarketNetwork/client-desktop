from __future__ import annotations
from ..wallet import coins
from collections.abc import Sequence
from threading import Lock
from typing import Iterator


class CoinList(Sequence):
    def __init__(self) -> None:
        self._lock = Lock
        self._list = (
            coins.Bitcoin(None),
            coins.BitcoinTest(None),
            coins.Litecoin(None),
        )

    def __len__(self) -> int:
        return len(self._list)

