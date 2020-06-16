
import logging
from datetime import datetime
from typing import Any, List, Mapping, Optional, Union

import PySide2.QtCore as qt_core

from .. import config
from . import db_entry, hd, key, mtx_impl, serialization, tx

log = logging.getLogger(__name__)


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
    txListChanged = qt_core.Signal()
    lastOffsetChanged = qt_core.Signal()
    useAsSourceChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()
    updatingChanged = qt_core.Signal()

    def __init__(self, name: str, coin: Optional["coins.CoinType"] = None):
        super().__init__(parent=coin)
        assert(name)
        self._set_object_name(name)
        self.coin = coin
        self._name = name
        self._label = None
        # user reminder
        self._message = None
        # timestamp
        self._created = None
        self._balance = 0.
        self._first_offset = None
        self._last_offset = None
        self._type = key.AddressType.P2PKH
        # use as source in current tx
        self._use_as_source = True
        self._unspents_time = qt_core.QTime()
        # lock
        self._updating_history = False
        #
        self._key = None
        # from server!!
        self._tx_count = None
        #
        self._tx_list = []
        self._valid = True
        # this map can be updated before each transaction
        self._unspents = []

    def to_table(self) -> dict:
        res = {
            "name": self._name,
            "type": self._type,
            "created": self._created.timestamp(),
        }
        if self._label:
            res["label"] = self._label
        if self._message:
            res["message"] = self._message
        if self._key:
            res["wif"] = self.export_key()
        return res

    def create(self):
        "fill NEW address"
        self._created = datetime.now()

    # no getter for it for security reasons
    def set_prv_key(self, value: Union[hd.HDNode, key.PrivateKey]) -> None:
        self._key = value

    @classmethod
    def from_table(cls, table: dict, coin: "coins.CoinType") -> "CAddress":
        w = cls(table["name"], coin)
        w.type = table["type"]
        w.label = table.get("label")
        w._message = table.get("message")
        # some fields can'be missed in some old backups
        w._created = datetime.fromtimestamp(
            table.get("created", datetime.now().timestamp()))
        if "wif" in table:
            w.import_key(table["wif"])
        return w

    @classmethod
    def make_from_hd(cls, hd_key: hd.HDNode, coin, type_: key.AddressType,
                     witver=0) -> "CAddress":
        res = cls(hd_key.to_address(type_, witver), coin)
        res.create()
        res._key = hd_key
        res.type = type_
        return res

    @property
    def coin(self) -> "coins.CoinType":
        return self._coin

    @coin.setter
    def coin(self, value: "CoinType"):
        self._coin = value
        if value:
            self._coin.heightChanged.connect(
                self.heightChanged, qt_core.Qt.UniqueConnection)

    @property
    def hd_index(self) -> Optional[int]:
        if self._key and isinstance(self._key, hd.HDNode):
            return self._key.index

    @property
    def type(self) -> key.AddressType:
        return self._type

    @type.setter
    def type(self, val: Union[str, key.AddressType]):
        if isinstance(val, (int, key.AddressType)):
            self._type = val
        else:
            self._type = key.AddressType.make(val)

    @property
    def unspents(self) -> List[mtx_impl.UTXO]:
        return self._unspents

    @unspents.setter
    def unspents(self, utxos: List[mtx_impl.UTXO]) -> None:
        self._unspents = utxos
        self._unspents_time.restart()
        balance = sum(int(u.amount) for u in self._unspents)
        if balance != self._balance:
            log.debug(
                f"Balance of {self} updated from {self._balance} to {balance}. Processed: {len(self._unspents)} utxo")
            # strict !!! remember notifiers
            self.balance = balance

    @property
    def wants_update_unspents(self) -> bool:
        return self._unspents_time.isNull() or self._unspents_time.elapsed() > self.UNSPENTS_TIMEOUT

    def process_unspents(self, unspents: List[dict]) -> None:
        def mapper(table):
            ux = mtx_impl.UTXO.from_net(
                amount=table["amount"],
                txindex=table["index"],
                txid=table["tx"],
                type=key.AddressType(self._type).lower,
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
            self._label = next(arg_iter)
            self._message = next(arg_iter)
            #
            self._created = datetime.fromtimestamp(next(arg_iter))
            self._type = next(arg_iter)
            self._balance = next(arg_iter)
            #
            self._tx_count = next(arg_iter)
            # use setters !!
            self.first_offset = next(arg_iter)
            self.last_offset = next(arg_iter)
            #
            self.import_key(next(arg_iter))
        except StopIteration as si:
            raise StopIteration(
                f"Too few arguments for address {self}") from si

    def match(self, pref: str) -> bool:
        return self._name.lower().startswith(pref.lower())

    def is_receiver(self, tx_: tx.Transaction) -> bool:
        return any(self.name == o.address for o in tx_.output_iter)

    def add_tx(self, tx_: "tx.Transaction"):
        """
        too heavy for multiple items

        important thing.. we call it when save from net only!!

        we should detect new money transfer !!!
        """
        # stick to the order !!
        # if any(t.name == tx_.name for t in self._tx_list):
        tx_ex = next((t for t in self._tx_list if t.name == tx_.name), None)
        if tx_ex:
            tx_ex.height = tx_.height
            tx_ex.time = tx_.time
            # we don't want to save it. it only for UI.. next session we'll get real TX
            raise tx.TxError(f"TX {tx_.name} already exists")
        # we need it for processing
        tx_._wallet = self
        # process not in main thread
        tx_.process()
        # now we have to do it before adopting
        tx_.moveToThread(self.thread())
        tx_.setParent(self)
        # detect income
        day = datetime.fromtimestamp(tx_.time).date()
        # if self.coin.height == tx_.height: # wrong condition
        if datetime.today().date() == day and self.is_receiver(tx_):
            from client.ui.gui import api
            ui = api.Api.get_instance()
            log.warning("send tx to ui")
            if ui:
                ui.coinManager.on_incoming_transfer(tx_)
        #
        self._tx_list.append(tx_)
        self._tx_list.sort(key=lambda tx: tx.time, reverse=True)
        self.txListChanged.emit()

    def add_tx_list(self, txs: list):
        """
        importnant thing.. we call it when load from DB!!!
        no processin here !!!
        """
        for tr in txs:
            if any(t.name == tr.name for t in self._tx_list):
                log.debug(f"tx doubled {tr}")
            # tx.process()
            tr.moveToThread(self.thread())
            tr.wallet = self
        self._tx_list.extend(txs)
        self._tx_list.sort(key=lambda tx: tx.time, reverse=True)
        self.txListChanged.emit()

    def make_dummy_tx(self) -> tx.Transaction:
        tx_ = tx.Transaction.make_dummy(self)
        tx_.parse("fffff0000_debug_000000fffff", {
            'height': self.coin.height - 100,
            'amount': 12000000,
            'fee': 50000,
            'time': datetime.now().timestamp(),
            'coinbase': 0,
            'input': [],
            'output': [],
        })
        self.insert_new(tx_)
        return tx_

    def insert_new(self, tx_: tx.Transaction):
        # insert on the top
        tx_.moveToThread(self.thread())
        tx_.wallet = self
        self._tx_list.insert(0, tx_)
        self.txListChanged.emit()

    def _get_first_offset(self) -> int:
        return self._first_offset or "best"

    def _set_first_offset(self, bh: int):
        self._first_offset = str(bh)

    def _get_last_offset(self) -> str:
        return self._last_offset or "best"

    def _set_last_offset(self, bh):
        if 'None' == bh:
            bh = None
        if bh == self._last_offset:
            return
        self._last_offset = str(bh)
        self.lastOffsetChanged.emit()

    def _get_tx_count(self) -> int:
        return self._tx_count

    def _set_tx_count(self, txc):
        if txc is not None:
            # log.debug("has tx_DB count  (%s from %s) for %s" , self._tx_db_count , txc , self)
            pass
        self._tx_count = txc

    def __str__(self) -> str:
        return f"<{self._coin.name}:{self._name} <{self._label}> [T:{self._type}] [key:{self._key}]>"

    def __repr__(self) -> str:
        return f"""<{self._coin.name}:{self._name} <{self._label}>[row:{self._rowid}; foff:{self._first_offset};loff:{self._last_offset}]{self._balance}>"""

    def __eq__(self, other: "CAddress") -> bool:
        if not isinstance(other, self.__class__):
            raise TypeError
        return self._name == other.name and \
            self._type == other.type and \
            self._last_offset == other.last_offset and \
            self._first_offset == other.first_offset and \
            True

    def _get_valid(self) -> bool:
        return self._valid

    def _set_valid(self, val: bool):
        self._valid = val

    def clear(self):
        self._tx_list.clear()
        self._first_offset = None
        self._last_offset = None
        self._tx_count = 0
        self.txListChanged.emit()

    @property
    def private_key(self) -> str:
        if isinstance(self._key, hd.HDNode):
            return self._key.key
        if isinstance(self._key, key.PrivateKey):
            return self._key

    def export_key(self) -> str:
        if self._key:
            if isinstance(self._key, hd.HDNode):
                return self._key.extended_key
            if isinstance(self._key, key.PrivateKey):
                return self._key.to_wif
            log.warn(f"Unknown key type {type(self._key)} in {self}")
        return ""

    def export_txs(self, path: str):
        ser = serialization.Serializator()
        ser.add_one("address", self)
        ser.add_many("transactions", self._tx_list)
        ser.to_file(path, pretty=True)

    def import_key(self, txt: str):
        """
        TODO:
        """
        if txt:
            try:
                self._key = hd.HDNode.from_extended_key(txt, self)
                assert self._coin.hd_node is None or self._key.p_fingerprint == self._coin.hd_node.fingerprint
            except hd.HDError:
                self._key = key.PrivateKey.from_wif(txt)
            log.debug(f"new key created for {self} => {self._key}")
            adrr = self._key.to_address(self._type)
            if self._name != adrr:
                raise AddressError(
                    f"HD generation failed: wrong result address: {adrr} for {self}")

    # qml bindings
    @qt_core.Property(bool, notify=updatingChanged)
    def isUpdating(self) -> bool:
        return self._updating_history

    @isUpdating.setter
    def _set_updating(self, val: bool) -> None:
        if val == self._updating_history:
            return
        self._updating_history = val
        self.updatingChanged.emit()

    @qt_core.Property(bool, notify=useAsSourceChanged)
    def useAsSource(self) -> bool:
        return self._use_as_source

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self._name

    @qt_core.Property(str, constant=True)
    def public_key(self) -> str:
        if self.private_key:
            return self.private_key.public_key.to_hex

    @qt_core.Property(str, constant=True)
    def to_wif(self) -> str:
        if self.private_key:
            return self.private_key.to_wif

    @qt_core.Property(int, notify=balanceChanged)
    def balance(self) -> int:
        return self._balance

    @qt_core.Property(str, notify=balanceChanged)
    def balanceHuman(self) -> str:
        return str(self._coin.balance_human(self._balance))

    @qt_core.Property(str, notify=balanceChanged)
    def fiatBalance(self) -> str:
        return str(self._coin.fiat_amount(self._balance))

    @balance.setter
    def _set_balance(self, bl: str):
        if bl == self._balance:
            return
        self._balance = bl
        self.balanceChanged.emit()
        self._coin.update_balance()

    @qt_core.Property(str, notify=labelChanged)
    def label(self) -> str:
        return self._label

    @label.setter
    def _set_label(self, lbl: str):
        if lbl == self._label:
            return
        self._label = lbl
        self.labelChanged.emit()

    @qt_core.Property(str, constant=True)
    def message(self) -> str:
        return self._message

    @qt_core.Property(str, constant=True)
    def created(self) -> str:
        return self._created.strftime("%x %X")

    @property
    def created_db_repr(self) -> int:
        if self._created:
            return int(self._created.timestamp())
        return 0

    @useAsSource.setter
    def _set_use_as_source(self, on: bool):
        if on == self._use_as_source:
            return
        self._use_as_source = on
        self.useAsSourceChanged.emit()

    @qt_core.Property('QVariantList', notify=txListChanged)
    def txs(self) -> List[db_entry.DbEntry]:
        return self._tx_list

    @qt_core.Property(bool, constant=True)
    def readOnly(self) -> bool:
        log.debug(f"key:{self._key}")
        return self._key is None or \
            isinstance(self._key, key.PublicKey)

    @qt_core.Slot()
    def save(self):
        self.gcd.save_wallet(self)

    @property
    def gcd(self) -> "GCD":
        return self._coin.parent()

    tx_count = property(_get_tx_count, _set_tx_count)
    first_offset = property(_get_first_offset, _set_first_offset)
    last_offset = property(_get_last_offset, _set_last_offset)
    valid = property(_get_valid, _set_valid)
