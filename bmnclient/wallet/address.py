from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Union

import PySide2.QtCore as qt_core

from . import hd, key

from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)

class AddressError(Exception):
    pass


class CAddress(AbstractCoin.Address):
    balanceChanged = qt_core.Signal()
    labelChanged = qt_core.Signal()
    useAsSourceChanged = qt_core.Signal()

    def __init__(
            self,
            coin: AbstractCoin,
            **kwargs):
        if kwargs["name"] is None:
            kwargs["name"] = "null"
        assert coin is not None

        super().__init__(coin, **kwargs)

        self.__created = None
        self.__type = key.AddressType.P2PKH
        # use as source in current tx
        self.__use_as_source = True
        # for ui .. this is always ON when goint_to_update ON but conversely
        self.__updating_history = False
        # to stop network stuff
        self.__deleted = False
        #
        self.__key = None
        # from server!!
        self.__tx_count = 0
        self.__valid = True

    def create(self):
        self.__created = datetime.now()

    # no getter for it for security reasons
    def set_prv_key(self, value: Union[hd.HDNode, key.PrivateKey]) -> None:
        self.__key = value

    @classmethod
    def make_from_hd(cls, hd__key: hd.HDNode, coin, type_: key.AddressType,
                     witver=0) -> "CAddress":
        res = cls(coin, name=hd__key.to_address(type_, witver))
        res.create()
        res.__key = hd__key
        res.type = type_
        return res

    @property
    def deleted(self) -> bool:
        return self.__deleted

    @property
    def hd_index(self) -> Optional[int]:
        if self.__key and isinstance(self.__key, hd.HDNode):
            return self.__key.index

    @property
    def type(self) -> key.AddressType:
        return self.__type

    @type.setter
    def type(self, val: Union[str, key.AddressType]):
        if isinstance(val, (int, key.AddressType)):
            self.__type = val
        else:
            self.__type = key.AddressType.make(val)

    def from_args(self, arg_iter: iter):
        try:
            self.rowId = next(arg_iter)
            self.label = next(arg_iter)
            self.comment = next(arg_iter)
            #
            self.__created = datetime.fromtimestamp(next(arg_iter))
            self.__type = next(arg_iter)
            self._amount = next(arg_iter)
            #
            self.__tx_count = next(arg_iter)
            # use setters !!
            self.historyFirstOffset = next(arg_iter)
            self.historyLastOffset = next(arg_iter)
            #
            self.import_key(next(arg_iter))
        except StopIteration as si:
            raise StopIteration(
                f"Too few arguments for address {self}") from si

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
            self.__type == other.type and \
            self._history_last_offset == other._history_last_offset and \
            self._history_first_offset == other._history_first_offset and \
            True

    def _get_valid(self) -> bool:
        return self.__valid

    def _set_valid(self, val: bool):
        self.__valid = val

    def clear(self):
        self._tx_list.clear()
        self._history_first_offset = None
        self._history_last_offset = None
        self.__tx_count = 0
        self.__deleted = True

    @property
    def private_key(self) -> str:
        if isinstance(self.__key, hd.HDNode):
            return self.__key.key
        if isinstance(self.__key, key.PrivateKey):
            return self.__key

    def export_key(self) -> str:
        if self.__key:
            if isinstance(self.__key, hd.HDNode):
                return self.__key.extended_key
            if isinstance(self.__key, key.PrivateKey):
                return self.__key.to_wif
            log.warn(f"Unknown key type {type(self.__key)} in {self}")
        return ""

    def import_key(self, txt: str):
        if txt:
            try:
                self.__key = hd.HDNode.from_extended_key(txt, self)
                assert self._coin.hdPath is None or self.__key.p_fingerprint == self._coin.hdPath.fingerprint
            except hd.HDError:
                self.__key = key.PrivateKey.from_wif(txt)
            # log.debug(f"new key created for {self} => {self.__key}")
            adrr = self.__key.to_address(self.__type)
            if self._name != adrr:
                log.critical(f"ex key: {txt} type: {self.__type}")
                raise AddressError(
                    f"HD generation failed: wrong result address: {adrr} != {self._name} for {self}")

    # qml bindings
    @property
    def isUpdating(self) -> bool:
        self.__deleted = False
        return self.__updating_history

    @isUpdating.setter
    def isUpdating(self, val: bool) -> None:
        if val == self.__updating_history:
            return
        self.__updating_history = bool(val)
        ##self._state_model.refresh()

    @property
    def useAsSource(self) -> bool:
        return self.__use_as_source

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
    def created(self) -> datetime:
        return self.__created

    @useAsSource.setter
    def _set_use_as_source(self, on: bool):
        if on == self.__use_as_source:
            return
        log.debug(f"{self} used as source => {on}")
        self.__use_as_source = on
        self.useAsSourceChanged.emit()

    # @qt_core.Property('QVariantList', constant=True)
    @property
    def tx_list(self) -> List:
        return list(self._tx_list)

    @property
    def readOnly(self) -> bool:
        return self.__key is None or \
            isinstance(self.__key, key.PublicKey)

    def save(self):
        from ..application import CoreApplication
        CoreApplication.instance().databaseThread.save_address(self)

    def __len__(self):
        return len(self._tx_list)

    def __getitem__(self, val: int) -> AbstractTx:
        return self._tx_list[val]

    valid = property(_get_valid, _set_valid)
