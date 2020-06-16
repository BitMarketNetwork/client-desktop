
import datetime
import enum
import logging
from typing import Iterable, List

import PySide2.QtCore as qt_core

from . import db_entry, serialization

log = logging.getLogger(__name__)


class TxError(Exception):
    pass


class TxStatus(enum.IntFlag):
    INCOMING = enum.auto()
    NOT_CONFIRMED = enum.auto()
    COINBASE = enum.auto()


class Transaction(db_entry.DbEntry, serialization.SerializeMixin):
    statusChanged = qt_core.Signal()
    # constant fields can be changed while reprocessing
    infoChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()

    def __init__(self, wallet: "CAddress"):
        super().__init__(parent=wallet)
        # setter !!!!
        self.wallet = wallet
        # use it for outputs too
        self._inputs = []
        # status
        self._status = TxStatus.INCOMING
        #
        self._from_address = None
        self._to_address = None
        self._height = 0

    @classmethod
    def make_dummy(cls, wallet: "CAddress") -> "Transaction":
        res = cls(wallet)
        return res

    def from_args(self, arg_iter: iter):
        """
                id,
                {self.name_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
                {self.status_column}
                {self.receiver_column},
                {self.target_column}
        """
        try:
            self._rowid = next(arg_iter)
            self._name = next(arg_iter)
            self._set_object_name(self._name)
            assert isinstance(self._name, str)
            self._height = next(arg_iter)
            self._time = next(arg_iter)
            self._balance = next(arg_iter)
            self._fee = next(arg_iter)
            self._status = next(arg_iter)
            self._from_address = next(arg_iter)
            self._to_address = next(arg_iter)
            self._inputs = []
            self._outputs = []
        except StopIteration:
            log.error("Too few arguments for TX {self}")

    def parse(self, name: str, body: dict):
        self._name = name
        self._set_object_name(name)
        # no heigth in mempool !
        self._height = body.get("height", None)
        self._time = body["time"]
        self._balance = body["amount"]
        self._fee = body["fee"]
        if body["coinbase"] != 0:
            self._status |= TxStatus.COINBASE
        # leave iterators
        self._inputs = map(lambda t: Input.from_dict(t, self), body["input"])
        self._outputs = map(
            lambda t: Output.from_dict(t, self), body["output"])

    def to_table(self) -> dict:
        return {
            "hash": self._name,
            "amount": self._balance,
            "fee": self._fee,
            "height": self._height,
            "time": self._time,
        }

    def process(self):
        """
        we have to use input's iterators so unpack it to the lists
        """
        if self._inputs is None:
            return
        # detect direction
        all_adds = self._wallet.coin.address_names
        self._outputs = list(self._outputs)
        self._inputs = list(self._inputs)
        # TODO:
        for out in self._outputs:
            if self._to_address is None:
                self._to_address = out.address
            if out.address not in all_adds:
                self._status &= ~TxStatus.INCOMING
                self.statusChanged.emit()
                break
        for inp in self._inputs:
            if self._from_address is None:
                self._from_address = inp.address
                break
        self.infoChanged.emit()

    def make_input(self, args: iter):
        type_ = next(args)
        if type_ == InputType.INPUT:
            inp = Input(None)
        elif type_ == InputType.OUTPUT:
            inp = Output(None)
        else:
            raise ValueError(f"Bad input type {type_}")
        inp.from_args(args, self)
        (self._inputs if type_ == InputType.INPUT else self._outputs).append(inp)

    def add_input(self, input: "InputType"):
        """
        and outputs too of course
        """
        if input.type == InputType.OUTPUT:
            self._outputs.append(input)
        else:
            self._inputs.append(input)

    @property
    def input_iter(self) -> Iterable["InputType"]:
        if isinstance(self._inputs, list):
            return iter(self._inputs)
        return self._inputs

    @property
    def output_iter(self) -> Iterable["InputType"]:
        if isinstance(self._outputs, list):
            return iter(self._outputs)
        return self._outputs

    @property
    def wallet(self) -> "CAddress":
        return self._wallet

    @wallet.setter
    def wallet(self, wall: "CAddress"):
        self._wallet = wall
        if wall:
            # self._wallet.heightChanged.connect(
            # self.heightChanged, qt_core.Qt.QueuedConnection)
            # self._wallet.heightChanged.connect( self.testHeight
            # , qt_core.Qt.QueuedConnection)
            self.setParent(wall)

    """
    DISABLED FOR A WHILE
    SEE TxListPanel.qml

    @qt_core.Slot()
    def testHeight(self):
        self.heightChanged.emit()
        log.error(f"height:{self.confirmCount} => {self._wallet.coin.height}")
        """

    @qt_core.Property(int, notify=heightChanged)
    def confirmCount(self) -> int:
        if self._height is not None \
                and self._wallet.coin.height:
            return self._wallet.coin.height - self._height + 1
        log.debug(f"no confirm: height:{self._height} => {self._wallet.coin.height}")
        return 0

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int):
        if self._height == value:
            return
        self._height = value
        self.heightChanged.emit()

    @property
    def base(self):
        return self._base

    @property
    def fee(self):
        return self._fee

    @fee.setter
    def fee(self, value: int):
        self._fee = value

    @property
    def time(self) -> int:
        return self._time

    @time.setter
    def time(self, value: int):
        self._time = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, st):
        if st == self._status:
            return
        self._status = st
        self.statusChanged.emit()

    def __str__(self):
        return self._name

    def __repr__(self):
        return f"{self._name} height:{self._height} amount:{self._balance} fee:{self._fee} time:{self._time}"

    def add_inputs(self, values: iter, in_type: bool = True):
        for amount, address in values:
            if in_type:
                inp = Input(self)
            else:
                inp = Output(self)
            inp._amount = amount
            inp._address = address
        self._inputs.append(inp)

        # qt bindings

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self._name

    @name.setter
    def _set_name(self, value: str):
        self._name = value

    @qt_core.Property("quint64", constant=True)
    def balance(self) -> int:
        return self._balance

    @balance.setter
    def _set_balance(self, value: int):
        self._balance = value

    @qt_core.Property(str, constant=True)
    def balanceHuman(self) -> str:
        return str(self._wallet._coin.balance_human(self._balance))

    @qt_core.Property(str, constant=True)
    def unit(self) -> str:
        return self._wallet._coin.unit

    @qt_core.Property(str, constant=True)
    def feeHuman(self) -> str:
        return str(self._wallet._coin.balance_human(self._fee))

    @qt_core.Property(str, constant=True)
    def fiatBalance(self) -> str:
        return str(self._wallet._coin.fiat_amount(self._balance))

    @qt_core.Property(bool, notify=statusChanged)
    def sent(self) -> bool:
        return (self._status & TxStatus.INCOMING) == 0

    @qt_core.Property(str, constant=True)
    def timeHuman(self) -> str:
        # return datetime.datetime.utcfromtimestamp(self._time).strftime("%x %X")
        return datetime.datetime.fromtimestamp(self._time).strftime("%x %X")

    @qt_core.Property(str, notify=infoChanged)
    def fromAddress(self) -> str:
        if self._from_address is None:
            return self.tr("Not detected")
        return self._from_address

    @fromAddress.setter
    def _set_from_address(self, adr: str):
        if adr == self._from_address:
            return
        self._from_address = adr
        self.infoChanged.emit()

    @qt_core.Property(str, notify=infoChanged)
    def toAddress(self) -> str:
        if self._to_address is None:
            return self.tr("Not detected")
        return self._to_address

    @toAddress.setter
    def _set_to_address(self, adr: str):
        if adr == self._to_address:
            return
        self._to_address = adr
        self.infoChanged.emit()

    @qt_core.Property(str, notify=heightChanged)
    def block(self) -> str:
        "can be none"
        if self._height is None:
            return "-"
        return str(self._height) 


class InputType(enum.IntFlag):
    """
    Keep it as flag for future use
    """
    INPUT = 0
    OUTPUT = 1


class Input:
    type = InputType.INPUT

    def __init__(self, tx: Transaction):
        self._tx = tx
        self._amount = None
        self._address = None

    @classmethod
    def from_dict(cls, table: dict, tx: Transaction = None):
        inp = cls(None)
        inp._amount = table["amount"]
        inp._address = table["address"]
        # inp.moveToThread(tx.thread())
        # inp.setParent(tx)
        inp._tx = tx
        return inp

    def from_args(self, arg_iter: Iterable, tx: Transaction):
        """
                !! type has been eaten by tx !!
                {self.address_column},
                {self.amount_column},
        """
        try:
            self._tx = tx
            self._address = next(arg_iter)
            self._amount = next(arg_iter)
        except StopIteration:
            log.error(f"Too few arguments for Input {self}")

    @property
    def address(self) -> str:
        return self._address

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def tx(self) -> "Transaction":
        return self._tx

    def __str__(self) -> str:
        return self._address


class OutputType(enum.IntEnum):
    NONSTANDART = enum.auto()
    PUBKEY = enum.auto()
    PUBKEYHASH = enum.auto()
    SCRIPTHASH = enum.auto()
    MULTISIG = enum.auto()
    NULLDATA = enum.auto()
    WITNESS_V0_KEYHASH = enum.auto()
    WITNESS_V0_SCRIPTHASH = enum.auto()
    WITNESS_UNKNOWN = enum.auto()


class Output(Input):
    type = InputType.OUTPUT

    def __init__(self, tx: Transaction):
        super().__init__(tx=tx)
        self._type = OutputType.NONSTANDART
