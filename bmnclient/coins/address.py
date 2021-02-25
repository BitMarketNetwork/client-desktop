# JOK++
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .coin import AbstractCoin
    from .tx import AbstractTx


class AddressModelInterface:
    def beforeAppendTx(self, tx: AbstractTx) -> None:
        raise NotImplementedError

    def afterAppendTx(self, tx: AbstractTx) -> None:
        raise NotImplementedError


class AbstractAddress:
    def __init__(self, data: bytes, *, coin: AbstractCoin) -> None:
        self._coin = coin
        self._data = data
        self._amount = 0
        self._tx_list = []

        self._model: Optional[AddressModelInterface] = \
            self._coin.model_factory(self)

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @property
    def model(self) -> Optional[AddressModelInterface]:
        return self._model

    @classmethod
    def decode(
            cls,
            source: str,
            *,
            coin: AbstractCoin) -> Optional[AbstractAddress]:
        return None

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def txList(self) -> List[AbstractTx]:
        return self._tx_list

    def findTxByName(self, name: str) -> Optional[AbstractTx]:
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for tx in self._tx_list:
            if name == tx.name.casefold():
                return tx
        return None

    def appendTx(self, tx: AbstractTx) -> bool:
        # TODO tmp, old wrapper
        if self.findTxByName(tx.name) is not None:  # noqa
            return False

        if self._model:
            self._model.beforeAppendTx(tx)
        self._tx_list.append(tx)
        if self._model:
            self._model.afterAppendTx(tx)

        return True
