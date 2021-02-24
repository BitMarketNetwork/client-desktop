# JOK++
from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from .tx import AbstractTx

if TYPE_CHECKING:
    from .coin import AbstractCoin


class AddressModelInterface:
    def beforeAppendTx(self, tx: AbstractTx) -> None:
        raise NotImplementedError

    def afterAppendTx(self, tx: AbstractTx) -> None:
        raise NotImplementedError


class AbstractAddress:
    class _Tx(AbstractTx):
        pass

    def __init__(
            self,
            data: bytes,
            *,
            coin: Optional[AbstractCoin] = None) -> None:
        self._coin = coin
        self._data = data
        self._amount = 0
        self._tx_list = []

        self._model: Optional[AddressModelInterface] = \
            None if self._coin is None else self._coin.model_factory(self)

    @property
    def model(self) -> Optional[AddressModelInterface]:
        return self._model

    @classmethod
    def decode(cls, source: str) -> Optional[AbstractAddress]:
        return None

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def txList(self) -> List[_Tx]:
        return self._tx_list

    def findTxByName(self, name: str) -> Optional[_Tx]:
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for tx in self._tx_list:
            if name == tx.name.casefold():
                return tx
        return None

    def putTx(self, tx: _Tx, *, check=True) -> bool:
        # TODO tmp, old wrapper
        if check and self.findTxByName(tx.name) is not None:  # noqa
            return False
        if tx.wallet is None:  # TODO tmp
            tx.wallet = self

        if self._model:
            self._model.beforeAppendTx(tx)
        self._tx_list.append(tx)
        if self._model:
            self._model.afterAppendTx(tx)

        return True
