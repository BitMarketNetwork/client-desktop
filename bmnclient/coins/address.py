# JOK++
from __future__ import annotations

from typing import List, Optional
from .tx import AbstractTx


class AddressModelInterface:
    # TODO
    pass


class AbstractAddress:
    class Tx(AbstractTx):
        pass

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._tx_list = []

    @property
    def model(self) -> Optional[AddressModelInterface]:
        # TODO
        return None

    @classmethod
    def decode(cls, source: str) -> Optional[AbstractAddress]:
        return None

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def txList(self) -> List[Tx]:
        return self._tx_list

    # TODO
    def findTxByName(self, name: str) -> Optional[Tx]:
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for tx in self._tx_list:
            if name == tx.name.casefold():
                return tx
        return None

    # TODO
    def putTx(self, tx: Tx, *, check=True) -> bool:
        # TODO tmp, old wrapper
        if check and self.findTxByName(tx.name) is not None:  # noqa
            return False
        if tx.wallet is None:  # TODO
            tx.wallet = self
        self._tx_list.append(tx)
        return True
