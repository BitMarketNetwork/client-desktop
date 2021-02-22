from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Optional, Union, TYPE_CHECKING

import PySide2.QtCore as qt_core

from . import db_entry, hd, key, mtx_impl
from ..models.address import AddressAmountModel, AddressStateModel
from ..models.tx import TransactionListModel, TransactionListSortedModel

if TYPE_CHECKING:
    from .tx import Transaction

log = logging.getLogger(__name__)


def offset_less(left: str, right: str) -> bool:
    if not left:
        return True
    l = left.partition('.')
    r = right.partition('.')
    # equality matters
    if int(l[0]) <= int(r[0]):
        return True
    if l[0] == r[0]:
        return int(l[2]) < int(r[2])
    return False


class AddressError(Exception):
    pass


class CAddress(db_entry.DbEntry):
    # get unspents once a minute
    UNSPENTS_TIMEOUT = 60000
    is_root = False
    """
    one entry in wallet
    """
    balanceChanged = qt_core.Signal()
    labelChanged = qt_core.Signal()
    lastOffsetChanged = qt_core.Signal()
    useAsSourceChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()
    #
    txCountChanged = qt_core.Signal()

    def __init__(self, name: str, coin: Optional["coins.CoinType"] = None, *, created: bool = False):
        super().__init__(parent=coin)
        assert(name)
        self._tx_list = []
        self._set_object_name(name)
        self.coin = coin
        self.__name = name
        self.__label = ""
        # user reminder
        self.__message = None
        # timestamp
        self.__created = None
        self.__balance = 0
        self.__first_offset = None
        self.__last_offset = None
        self.__type = key.AddressType.P2PKH
        # use as source in current tx
        self.__use_as_source = True
        self.__unspents_time = qt_core.QTime()
        # for back
        self.__going_to_update = False
        # for ui .. this is always ON when goint_to_update ON but conversely
        self.__updating_history = False
        # to stop network stuff
        self.__deleted = False
        #
        self.__just_created = created
        #
        self.__key = None
        # from server!!
        self.__tx_count = 0
        self.__local__tx_count = 0
        #
        self.__valid = True
        # this map can be updated before each transaction
        self.__unspents = []

    @property
    def amountModel(self) -> AddressAmountModel:
        return self._amount_model

    @property
    def stateModel(self) -> AddressStateModel:
        return self._state_model

    @property
    def txListModel(self) -> TransactionListModel:
        return self._tx_list_model

    def txListSortedModel(self) -> TransactionListSortedModel:
        return TransactionListSortedModel(self._tx_list_model)

    def create(self):
        self.__created = datetime.now()

    # no getter for it for security reasons
    def set_prv_key(self, value: Union[hd.HDNode, key.PrivateKey]) -> None:
        self.__key = value

    @classmethod
    def make_from_hd(cls, hd__key: hd.HDNode, coin, type_: key.AddressType,
                     witver=0) -> "CAddress":
        res = cls(hd__key.to_address(type_, witver), coin, created=True)
        res.create()
        res.__key = hd__key
        res._state_model.refresh()
        res.type = type_
        return res

    @property
    def coin(self) -> "coins.CoinType":
        return self._coin

    @property
    def deleted(self) -> bool:
        return self.__deleted

    @coin.setter
    def coin(self, value: "CoinType"):
        self._coin = value
        if value is None:
            return
        from ..ui.gui import Application
        self._amount_model = AddressAmountModel(Application.instance(), self)
        self._amount_model.moveToThread(Application.instance().thread())
        self._state_model = AddressStateModel(Application.instance(), self)
        self._state_model.moveToThread(Application.instance().thread())
        self._tx_list_model = TransactionListModel(Application.instance(), self._tx_list)
        self._tx_list_model.moveToThread(Application.instance().thread())

        self._coin.heightChanged.connect(
            self.heightChanged, qt_core.Qt.UniqueConnection)

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

    @property
    def unspents(self) -> List[mtx_impl.UTXO]:
        return self.__unspents

    @unspents.setter
    def unspents(self, utxos: List[mtx_impl.UTXO]) -> None:
        self.__unspents = utxos
        self.__unspents_time.restart()

        def summ(u):
            u.address = self
            return int(u.amount)
        balance = sum(map(summ, self.__unspents))
        if balance != self.__balance:
            log.debug(
                f"Balance of {self} updated from {self.__balance} to {balance}. Processed: {len(self.__unspents)} utxo")
            # strict !!! remember notifiers
            self.balance = balance

    @property
    def wants_update_unspents(self) -> bool:
        return self.__unspents_time.isNull() or self.__unspents_time.elapsed() > self.UNSPENTS_TIMEOUT

    def process_unspents(self, unspents: List[dict]) -> None:
        def mapper(table):
            ux = mtx_impl.UTXO.from_net(
                amount=table["amount"],
                txindex=table["index"],
                txid=table["tx"],
                type=key.AddressType(self.__type).lower,
                address=self,
            )
            if ux.amount > 0:
                return ux
        self.unspents = [u for u in map(mapper, unspents) if u]

    def from_args(self, arg_iter: iter):
        """
            id,
            {self.label_column},
            {self.message_column},
            #
            {self.created_column},
            {self.type_column},
            {self.balance_column},
            #
            {self.tx_count_column},
            {self.first_offset_column},
            {self.last_offset_column}
            #
            key
        """
        try:
            self._rowid = next(arg_iter)
            self.__label = next(arg_iter)
            self.__message = next(arg_iter)
            #
            self.__created = datetime.fromtimestamp(next(arg_iter))
            self.__type = next(arg_iter)
            self.__balance = next(arg_iter)
            #
            self.__tx_count = next(arg_iter)
            # use setters !!
            self.first_offset = next(arg_iter)
            self.last_offset = next(arg_iter)
            #
            self.import_key(next(arg_iter))
        except StopIteration as si:
            raise StopIteration(
                f"Too few arguments for address {self}") from si

    def match(self, pref: str) -> bool:
        return self.__name.lower().startswith(pref.lower())

    def is_receiver(self, tx: Transaction) -> bool:
        return any(self.name == o.address for o in tx.output_iter)

    def add_tx(self, tx: Transaction, check_new=False):
        """
        too heavy for multiple items

        important thing.. we call it from mempool only!!!!
        """
        if tx in self._tx_list:
            tx_ex = next(
                (t for t in self._tx_list if t.name == tx.name), None)
            tx_ex.height = tx.height
            tx_ex.time = tx.time
            if not tx.local:
                # TODO: failure
                # should be decremented for each approved address
                self.__local__tx_count = 0
            tx_ex.local = False
            # we don't want to save it. it only for UI.. next session we'll get real TX
            self.txCountChanged.emit()
            raise tx.TxError("TX already exists")
        if tx.local:
            self.__local__tx_count += 1
        if check_new:
            from ..ui.gui import Application
            api_ = Application.instance()
            if api_:
                api_.uiManager.process_incoming_tx(tx)
        with self._tx_list_model.lockInsertRows():
            self._tx_list.append(tx)
            if tx.wallet is None:
                tx.wallet = self
        self.txCountChanged.emit()

    def add_tx_list(self, txs: list, check_new=False):
        """
        pay attention !! this scope very important
        """
        unique = []
        not_unique = []
        for tx in txs:
            if tx in self._tx_list:
                not_unique.append(tx)
            else:
                unique.append(tx)
        if not_unique:
            log.debug(f"TX DOUBLES: {len(not_unique)}")
        txs[:] = unique
        with self._tx_list_model.lockInsertRows(-1, len(unique)):
            for tx in unique:
                self._tx_list.append(tx)
        if check_new:
            from ..ui.gui import Application
            Application.instance().uiManager.process_incoming_tx(unique)

    def _get_first_offset(self) -> int:
        return self.__first_offset

    def _set_first_offset(self, bh: int):
        self.__first_offset = str(bh)

    def update_tx_list(self, first_offset: Optional[int], clear_tx_from: Optional[int], verbose: bool):
        self.__first_offset = first_offset
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
                with self._tx_list_model.lockRemoveRows(0, len(to_remove)):
                    self._tx_list.remove(0, len(to_remove))
                self.txCount -= len(to_remove)
                if verbose:
                    log.debug(
                        f"{len(to_remove)} tx were removed and {len(self._tx_list)} left in {self} ")

    def _get_last_offset(self) -> str:
        return self.__last_offset

    def _set_last_offset(self, bh):
        if not bh or 'None' == bh:
            return
        if bh == self.__last_offset:
            return
        if isinstance(bh, str):
            if not self.__last_offset or offset_less(bh, self.__last_offset):
                self.__last_offset = bh
                self.lastOffsetChanged.emit()
                return
        else:
            raise TypeError(type(bh))
        log.warning("Offsset skipped")

    @property
    def realTxCount(self) -> int:
        return len(self._tx_list)

    @qt_core.Property(int, notify=txCountChanged)
    def txCount(self) -> int:
        return self.__tx_count + self.__local__tx_count

    @txCount.setter
    def _set_tx_count(self, txc: int):
        if txc == self.__tx_count:
            return
        self.__tx_count = txc
        self.txCountChanged.emit()

    def __str__(self) -> str:
        return f"<{self._coin.name}:{self.__name} <{self.__label}> [T:{self.__type}] [key:{self.__key}]>"

    def __bool__(self) -> bool:
        return self is not None

    def __repr__(self) -> str:
        return f"""<{self._coin.name if self._coin is not None else 'none'}:{self.__name} <{self.__label}>[row:{self._rowid}; foff:{self.__first_offset};loff:{self.__last_offset}]{self.__balance}>"""

    def __hash__(self):
        return hash(self.__name)

    def __eq__(self, other: "CAddress") -> bool:
        if other is None or not isinstance(other, CAddress):
            return False
        return self.__name == other.name and \
            self.__type == other.type and \
            self.__last_offset == other.last_offset and \
            self.__first_offset == other.first_offset and \
            True

    def _get_valid(self) -> bool:
        return self.__valid

    def _set_valid(self, val: bool):
        self.__valid = val

    def clear(self):
        self._tx_list.clear()
        self.__first_offset = None
        self.__last_offset = None
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
        """
        TODO:
        """
        if txt:
            try:
                self.__key = hd.HDNode.from_extended_key(txt, self)
                assert self._coin.hd_node is None or self.__key.p_fingerprint == self._coin.hd_node.fingerprint
            except hd.HDError:
                self.__key = key.PrivateKey.from_wif(txt)
            # log.debug(f"new key created for {self} => {self.__key}")
            adrr = self.__key.to_address(self.__type)
            if self.__name != adrr:
                log.critical(f"ex key: {txt} type: {self.__type}")
                raise AddressError(
                    f"HD generation failed: wrong result address: {adrr} != {self.__name} for {self}")

    # qml bindings
    @qt_core.Property(bool)
    def isUpdating(self) -> bool:
        self.__deleted = False
        return self.__updating_history

    @isUpdating.setter
    def _set_updating(self, val: bool) -> None:
        if val:
            self.__going_to_update = True
        if val == self.__updating_history:
            return
        self.__updating_history = bool(val)
        self._state_model.refresh()

    @property
    def is_going_update(self) -> bool:
        return self.__going_to_update

    @is_going_update.setter
    def is_going_update(self, val: bool) -> None:
        self.__going_to_update = val

    @qt_core.Property(bool, notify=useAsSourceChanged)
    def useAsSource(self) -> bool:
        return self.__use_as_source

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self.__name

    @qt_core.Property(str, constant=True)
    def public_key(self) -> str:
        if self.private_key:
            return self.private_key.public__key.to_hex

    @qt_core.Property(str, constant=True)
    def to_wif(self) -> str:
        if self.private_key:
            return self.private_key.to_wif

    @property
    def empty_balance(self) -> bool:
        return not self.__just_created and self.__balance == 0

    def set_old(self):
        self.__just_created = False

    @qt_core.Property("qint64", notify=balanceChanged)
    def balance(self) -> int:
        return self.__balance

    @qt_core.Property(bool, notify=balanceChanged)
    def canSend(self) -> bool:
        return not self.readOnly and self.__balance > 0

    @qt_core.Property(bool, constant=True)
    def isRoot(self) -> bool:
        return self.is_root

    @balance.setter
    def _set_balance(self, bl: str):
        if bl == self.__balance:
            return
        self.__balance = bl
        self.balanceChanged.emit()
        self._amount_model.refresh()
        if self._coin is not None:
            self._coin.update_balance()

    @qt_core.Property(str, notify=labelChanged)
    def label(self) -> str:
        return self.__label or ""

    @label.setter
    def _set_label(self, lbl: str):
        if lbl == self.__label:
            return
        self.__label = lbl
        self.labelChanged.emit()

    @qt_core.Property(str, constant=True)
    def message(self) -> str:
        return self.__message

    @qt_core.Property(str, constant=True)
    def created_str(self) -> str:
        return self.__created.strftime("%x %X")

    @property
    def created(self) -> datetime:
        return self.__created

    @property
    def created_db_repr(self) -> int:
        if self.__created:
            return int(self.__created.timestamp())
        return 0

    @useAsSource.setter
    def _set_use_as_source(self, on: bool):
        if on == self.__use_as_source:
            return
        log.debug(f"{self} used as source => {on}")
        self.__use_as_source = on
        self.useAsSourceChanged.emit()

    # @qt_core.Property('QVariantList', constant=True)
    @property
    def tx_list(self) -> List[db_entry.DbEntry]:
        return list(self._tx_list)

    @qt_core.Property(bool, constant=True)
    def readOnly(self) -> bool:
        return self.__key is None or \
            isinstance(self.__key, key.PublicKey)

    @qt_core.Slot()
    def save(self):
        from ..application import CoreApplication
        CoreApplication.instance().databaseThread.save_wallet(self)

    def __len__(self):
        return len(self._tx_list)

    def __getitem__(self, val: int) -> Transaction:
        return self._tx_list[val]

    first_offset = property(_get_first_offset, _set_first_offset)
    last_offset = property(_get_last_offset, _set_last_offset)
    valid = property(_get_valid, _set_valid)
