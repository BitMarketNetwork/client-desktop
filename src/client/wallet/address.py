
import functools
import logging
from datetime import datetime
from typing import Any, List, Mapping, Optional, Union

import PySide2.QtCore as qt_core

from .. import config, orderedset
from . import db_entry, hd, key, mtx_impl, serialization, tx, util

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


class CAddress(db_entry.DbEntry, serialization.SerializeMixin):
    # get unspents once a minute
    UNSPENTS_TIMEOUT = 60000
    """
    one entry in wallet
    """
    balanceChanged = qt_core.Signal()
    labelChanged = qt_core.Signal()
    lastOffsetChanged = qt_core.Signal()
    useAsSourceChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()
    updatingChanged = qt_core.Signal()
    #
    addTx = qt_core.Signal()
    addTxList = qt_core.Signal(int, arguments=["count"])
    addComplete = qt_core.Signal()
    removeTxList = qt_core.Signal(int, arguments=["count"])
    removeComplete = qt_core.Signal()
    txCountChanged = qt_core.Signal()
    realTxCountChanged = qt_core.Signal()

    def __init__(self, name: str, coin: Optional["coins.CoinType"] = None, *, created: bool = False):
        super().__init__(parent=coin)
        assert(name)
        self._set_object_name(name)
        self.coin = coin
        self.__name = name
        self.__label = ""
        # user reminder
        self.__message = None
        # timestamp
        self.__created = None
        self.__balance = 0.
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
        self.__tx_list = orderedset.OrderedSet()
        self.__valid = True
        # this map can be updated before each transaction
        self.__unspents = []
        self.__connect_tx_model()

    def __connect_tx_model(self):
        from ..ui.gui import api
        api_ = api.Api.get_instance()
        if api_:
            model = api_.coinManager.txModel
            self.addTx.connect(functools.partial(model.append, self))
            self.addTxList.connect(functools.partial(model.append_list, self))
            self.addComplete.connect(
                functools.partial(model.append_complete, self))
            self.removeTxList.connect(
                functools.partial(model.remove_list, self))
            self.removeComplete.connect(
                functools.partial(model.remove_complete, self))

    def to_table(self) -> dict:
        res = {
            "name": self.__name,
            "type": self.__type,
            "created": self.__created.timestamp(),
        }
        if self.__label:
            res["label"] = self.__label
        if self.__message:
            res["message"] = self.__message
        if self.__key:
            res["wif"] = self.export__key()
        return res

    def create(self):
        "fill NEW address"
        self.__created = datetime.now()

    # no getter for it for security reasons
    def set_prv_key(self, value: Union[hd.HDNode, key.PrivateKey]) -> None:
        self.__key = value

    @classmethod
    def from_table(cls, table: dict, coin: "coins.CoinType") -> "CAddress":
        w = cls(table["name"], coin)
        w.type = table["type"]
        w.label = table.get("label")
        w.__message = table.get("message")
        # some fields can'be missed in some old backups
        w.__created = datetime.fromtimestamp(
            table.get("created", datetime.now().timestamp()))
        if "wif" in table:
            w.import_key(table["wif"])
        return w

    @classmethod
    def make_from_hd(cls, hd__key: hd.HDNode, coin, type_: key.AddressType,
                     witver=0) -> "CAddress":
        res = cls(hd__key.to_address(type_, witver), coin, created=True)
        res.create()
        res.__key = hd__key
        res.updatingChanged.emit()
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
        if value:
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

    def fill_with_dummy_unspents(self, balance: int):
        log.warning(f"Filling {self} with fake utxo on {self.__balance}")
        self.unspents = [
            mtx_impl.UTXO.make_dummy(balance, self)
        ]

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

    def is_receiver(self, tx_: tx.Transaction) -> bool:
        return any(self.name == o.address for o in tx_.output_iter)

    def add_tx(self, tx_: "tx.Transaction"):
        """
        too heavy for multiple items

        important thing.. we call it from mempool!!!!
        """
        if tx_ in self.__tx_list:
            tx_ex = next(
                (t for t in self.__tx_list if t.name == tx_.name), None)
            tx_ex.height = tx_.height
            tx_ex.time = tx_.time
            if not tx_.local:
                # TODO: failure
                # should be decremented for each approved address
                self.__local__tx_count = 0
            tx_ex.local = False
            # we don't want to save it. it only for UI.. next session we'll get real TX
            self.txCountChanged.emit()
            raise tx.TxError("TX already exists")
        if tx_.local:
            self.__local__tx_count += 1
        # we need it for processing
        # tx_._wallet = self
        # tx_.moveToThread(self.thread())
        # tx_.setParent(self)
        # detect income
        # day = datetime.fromtimestamp(tx_.time).date()
        # # if self.coin.height == tx_.height: # wrong condition
        # if False and datetime.today().date() == day and self.is_receiver(tx_):
        #     from client.ui.gui import api
        #     ui = api.Api.get_instance()
        #     log.warning("send tx to ui")
        #     if ui:
        #         ui.coinManager.on_incoming_transfer(tx_)
        #
        self.addTx.emit()
        self.__tx_list.raw_add(tx_, 0)
        if tx_.wallet is None:
            tx_.wallet = self
        self.addComplete.emit()
        self.txCountChanged.emit()
        self.realTxCountChanged.emit()

    def add_tx_list(self, txs: list):
        unique = []
        not_unique = []
        for tx in txs:
            if tx in self.__tx_list:
                not_unique.append(tx)
            else:
                unique.append(tx)
        if not_unique:
            log.debug(f"TX DOUBLES: {len(not_unique)}")
        txs[:] = unique
        self.addTxList.emit(len(unique))
        for tx in unique:
            self.__tx_list.raw_add(tx, 0)
        self.addComplete.emit()
        self.realTxCountChanged.emit()

    def make_dummy_tx(self, parent=None) -> tx.Transaction:
        tx_ = tx.Transaction.make_dummy(parent)
        name = util.random_hex(32)
        tx_.parse(name, {
            'height': self.coin.height or 0 + 1,
            'amount': 12000000,
            'fee': 50000,
            'time': datetime.now().timestamp(),
            'coinbase': 0,
            'input': [],
            'output': [],
        })
        if parent:
            parent.txCount += 1
        return tx_

    def _get_first_offset(self) -> int:
        return self.__first_offset

    def _set_first_offset(self, bh: int):
        self.__first_offset = str(bh)

    def update_tx_list(self, first_offset: Optional[int], clear_tx_from: Optional[int], verbose: bool):
        self.__first_offset = first_offset
        if clear_tx_from is not None:
            to_remove = []
            for k in self.__tx_list:
                if k.height > clear_tx_from:
                    to_remove += [k]
                else:
                    break
            if to_remove:
                self.gcd.removeTxList.emit(to_remove)
                self.removeTxList.emit(len(to_remove))
                self.__tx_list.remove(0, len(to_remove))
                self.removeComplete.emit()
                self.txCount -= len(to_remove)
                if verbose:
                    log.debug(
                        f"{len(to_remove)} tx were removed and {len(self.__tx_list)} left in {self} ")

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

    @qt_core.Property(int, notify=realTxCountChanged)
    def realTxCount(self) -> int:
        return len(self.__tx_list)

    @qt_core.Property(int, notify=txCountChanged)
    def txCount(self) -> int:
        return self.__tx_count + self.__local__tx_count

    @qt_core.Property(int, notify=txCountChanged)
    def safeTxCount(self) -> int:
        return max(len(self.__tx_list), self.txCount)

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
        return f"""<{self._coin.name if self._coin else 'none'}:{self.__name} <{self.__label}>[row:{self._rowid}; foff:{self.__first_offset};loff:{self.__last_offset}]{self.__balance}>"""

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
        self.__tx_list.clear()
        self.__first_offset = None
        self.__last_offset = None
        self.__tx_count = 0
        self.__deleted = True
        self.realTxCountChanged.emit()

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

    def export_txs(self, path: str):
        ser = serialization.Serializator()
        ser.add_one("address", self)
        ser.add_many("transactions", self.__tx_list)
        ser.to_file(path, pretty=True)

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
    @qt_core.Property(bool, notify=updatingChanged)
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
        self.updatingChanged.emit()

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
        if self.private__key:
            return self.private__key.public__key.to_hex

    @qt_core.Property(str, constant=True)
    def to_wif(self) -> str:
        if self.private__key:
            return self.private__key.to_wif

    @property
    def empty_balance(self) -> bool:
        # log.warning(f"new:{self.__just_created} b:{self.__balance}")
        return not self.__just_created and self.__balance == 0

    def set_old(self):
        self.__just_created = False

    @qt_core.Property("qint64", notify=balanceChanged)
    def balance(self) -> int:
        return self.__balance

    @qt_core.Property(str, notify=balanceChanged)
    def balanceHuman(self) -> str:
        return str(self._coin.balance_human(self.__balance))

    @qt_core.Property(str, notify=balanceChanged)
    def fiatBalance(self) -> str:
        return str(self._coin.fiat_amount(self.__balance))

    @balance.setter
    def _set_balance(self, bl: str):
        if bl == self.__balance:
            return
        self.__balance = bl
        self.balanceChanged.emit()
        if self._coin:
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
        return list(self.__tx_list)

    @qt_core.Property(bool, constant=True)
    def readOnly(self) -> bool:
        return self.__key is None or \
            isinstance(self.__key, key.PublicKey)

    @qt_core.Slot()
    def save(self):
        self.gcd.save_wallet(self)

    @property
    def gcd(self) -> "GCD":
        return self._coin.parent()

    def __len__(self):
        return len(self.__tx_list)

    def __getitem__(self, val: int) -> tx.Transaction:
        return self.__tx_list[val]

    first_offset = property(_get_first_offset, _set_first_offset)
    last_offset = property(_get_last_offset, _set_last_offset)
    valid = property(_get_valid, _set_valid)
