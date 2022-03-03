from __future__ import annotations

from typing import TYPE_CHECKING

from .coin import Coin
from .object import CoinObject, CoinObjectModel

if TYPE_CHECKING:
    from .object import CoinModelFactory
