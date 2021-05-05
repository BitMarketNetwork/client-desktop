from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from . import hd, key

from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)

class AddressError(Exception):
    pass


class CAddress(AbstractCoin.Address):
    def is_receiver(self, tx: AbstractCoin.Tx) -> bool:
        return any(self.name == o.address for o in tx.output_iter)

    def update_tx_list(self, first_offset: Optional[int], clear_tx_from: Optional[int], verbose: bool):
        self._history_first_offset = first_offset
        if clear_tx_from is not None:
            to_remove = []
            for k in self._tx_list:
                if k.height > clear_tx_from:
                    to_remove += [k]
                else:
                    break
            if to_remove:
                from ..application import CoreApplication
                CoreApplication.instance().databaseThread.removeTxList.emit(to_remove)
                with self.model.txList.lockRemoveRows(0, len(to_remove)):
                    # TODO
                    #self._tx_list.remove(0, len(to_remove))
                    pass
                #self.txCount -= len(to_remove)
                if verbose:
                    log.debug(
                        f"{len(to_remove)} tx were removed and {len(self._tx_list)} left in {self} ")

    @property
    def realTxCount(self) -> int:
        return len(self._tx_list)

    def __bool__(self) -> bool:
        return self is not None

    def __hash__(self):
        return hash(self._name)

    def __eq__(self, other: "CAddress") -> bool:
        if other is None or not isinstance(other, CAddress):
            return False
        return self._name == other.name and \
            self._type == other._type and \
            self._history_last_offset == other._history_last_offset and \
            self._history_first_offset == other._history_first_offset and \
            True

    def clear(self):
        self._tx_list.clear()
        self._history_first_offset = None
        self._history_last_offset = None

    @property
    def private_key(self) -> str:
        if isinstance(self._private_key, hd.HDNode):
            return self._private_key.key
        if isinstance(self._private_key, key.PrivateKey):
            return self._private_key

    def export_key(self) -> str:
        if self._private_key:
            if isinstance(self._private_key, hd.HDNode):
                return self._private_key.extended_key
            if isinstance(self._private_key, key.PrivateKey):
                return self._private_key.to_wif
            log.warn(f"Unknown key type {type(self._private_key)} in {self}")
        return ""

    @property
    def public_key(self) -> str:
        if self.private_key:
            return self.private_key.public__key.to_hex

    @property
    def to_wif(self) -> str:
        if self.private_key:
            return self.private_key.to_wif

    @property
    def canSend(self) -> bool:
        return not self.readOnly and self._amount > 0

    @property
    def readOnly(self) -> bool:
        return self._private_key is None or \
            isinstance(self._private_key, key.PublicKey)
