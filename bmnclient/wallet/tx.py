
import datetime
import enum
import logging
from typing import Iterable, List, Optional, Tuple

import PySide2.QtCore as qt_core

from . import db_entry, input_model, serialization

log = logging.getLogger(__name__)


class TxError(Exception):
    pass


class Transaction(db_entry.DbEntry, serialization.SerializeMixin):
    READY_CONFIRM_COUNT = 6
    statusChanged = qt_core.Signal()
    # constant fields can be changed while reprocessing
    infoChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()

    def __init__(self, wallet: "CAddress"):

        # wallet can be none for handmade tx
        # assert wallet is not None

        super().__init__(parent=None)
        self.__wallet = wallet
        self.__inputs = []
        self.__outputs = []
        self.__coin_base = False
        self.__height = 0
        self.__local = False
        self.__input_model = input_model.InputModel(self, True)
        self.__output_model = input_model.InputModel(self, False)

    @classmethod
    def make_dummy(cls, wallet: Optional["CAddress"]) -> "Transaction":
        res = cls(wallet)
        res.__local = True
        return res

    def from_args(self, arg_iter: iter):
        """
                id,
                {self.name_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
        """
        try:
            self._rowid = next(arg_iter)
            self.__name = next(arg_iter)
            self._set_object_name(self.__name)
            assert isinstance(self.__name, str)
            self.__height = next(arg_iter)
            self.__time = next(arg_iter)
            self.__balance = next(arg_iter)
            self.__fee = next(arg_iter)
            self.__inputs = []
            self.__outputs = []
        except StopIteration:
            log.error("Too few arguments for TX {self}")

    def parse(self, name: str, body: dict):
        self.__name = name
        self._set_object_name(name)
        # no heigth in mempool !
        self.__height = body.get("height", None)
        self.__time = body["time"]
        self.__balance = body["amount"]
        self.__fee = body["fee"]
        self.__coin_base = body["coinbase"] != 0
        # leave iterators !!!
        self.__inputs = map(lambda t: Input.from_dict(t, self), body["input"])
        self.__outputs = map(
            lambda t: Output.from_dict(t, self), body["output"])
        return self

    def dump(self) -> dict:
        assert self.__wallet
        res = {
            "time": self.__time,
            "amount": self.__balance,
            "fee": self.__fee,
            "coinbase": 1 if self.__coin_base else 0,
            # TODO
            "input": [
                i.dump() for i in self.inputs
            ],
            "output": [
                i.dump() for i in self.outputs
            ],
        }
        if self.__height is not None:
            res.update({
                "height": self.__height
            })
        return res

    def to_table(self) -> dict:
        return {
            "hash": self.__name,
            "amount": self.__balance,
            "fee": self.__fee,
            "height": self.__height,
            "time": self.__time,
        }

    def make_input(self, args: iter):
        if next(args):
            inp = Output(self)
            if not isinstance(self.__outputs, list):
                self.__outputs = list(self.__outputs)
            self.__outputs.append(inp)
        else:
            inp = Input(self)
            if not isinstance(self.__inputs, list):
                self.__inputs = list(self.__inputs)
            self.__inputs.append(inp)
        inp.from_args(args)
        # inp.moveToThread(self.thread())
        # inp.tx = self

    @property
    def wallet(self) -> "CAddress":
        return self.__wallet

    @property
    def local(self) -> bool:
        return self.__local

    @local.setter
    def local(self, on: bool) -> None:
        self.__local = on

    @wallet.setter
    def wallet(self, wall: "CAddress"):
        self.__wallet = wall
        if wall:
            self.__wallet.heightChanged.connect(
                self.heightChanged, qt_core.Qt.QueuedConnection)
        # self.setParent(wall)

    """
    DISABLED FOR A WHILE
    SEE TxListPanel.qml

    @qt_core.Slot()
    def testHeight(self):
        self.heightChanged.emit()
        log.error(f"height:{self.confirmCount} => {self.__wallet.coin.height}")
        """

    @property
    def coin_base(self) -> int:
        return 1 if self.__coin_base else 0

    @qt_core.Property(int, notify=heightChanged)
    def confirmCount(self) -> int:
        if self.__height is not None \
                and self.__wallet.coin.height:
            return max(0, self.__wallet.coin.height - self.__height + 1)
        log.debug(
            f"no confirm: height:{self.__height} => {self.__wallet.coin.height}")
        return 0

    @qt_core.Property(qt_core.QObject, constant=True)
    def inputsModel(self) -> qt_core.QObject:
        return self.__input_model

    @qt_core.Property(qt_core.QObject, constant=True)
    def outputsModel(self) -> qt_core.QObject:
        return self.__output_model

    @property
    def height(self) -> int:
        return self.__height

    @height.setter
    def height(self, value: Optional[int]):
        if self.__height == value:
            return
        self.__height = value
        self.heightChanged.emit()
        self.statusChanged.emit()

    @property
    def base(self) -> bool:
        return self.__coin_base

    @property
    def fee(self) -> int:
        return self.__fee

    @fee.setter
    def fee(self, value: int):
        self.__fee = value

    @property
    def time(self) -> int:
        return self.__time

    @time.setter
    def time(self, value: int):
        self.__time = value

    def size(self, inp: bool) -> int:
        return len(self.inputs) if inp else len(self.outputs)

    def get(self, index: int, inp: bool):
        return self.inputs[index] if inp else self.outputs[index]

    def __eq__(self, other):
        if isinstance(other, Transaction):
            return self.__name == other.__name
        raise TypeError

    def __hash__(self):
        return hash(self.__name)

    def __str__(self):
        return self.__name

    def __repr__(self):
        return f"{self.__name} height:{self.__height} amount:{self.__balance} fee:{self.__fee} time:{self.__time} \
            in.count:{len(self.inputs)} out.count: {len(self.outputs)}"

    def user_view(self, sett) -> str:
        # return self.tr(f"Transaction '%s' from %s. Amount: %s") % (self.__name, self.timeHuman, self.__balance)
        return self.tr(f"Transaction of %s. Amount: %s %s") % (self.timeHuman,
                                                               sett.coinBalance(
                                                                   self.__balance),
                                                               sett.coinUnit(self.__wallet.coin.unit))

    def add_inputs(self, values: iter, in_type: bool = True):
        # import pdb; pdb.set_trace()
        for amount, address in values:
            if in_type:
                inp = Input(self)
                self.inputs.append(inp)
            else:
                inp = Output(self)
                self.outputs.append(inp)
            inp.amount = amount
            inp.address = address

        # qt bindings

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self.__name

    @property
    def inputs(self) -> list:
        if not isinstance(self.__inputs, list):
            self.__inputs = list(self.__inputs)
        return self.__inputs

    # @qt_core.Property("QVariantList", constant=True)
    # def inputsModel(self) -> list:
    #     return self.inputs

    @property
    def outputs(self) -> list:
        if not isinstance(self.__outputs, list):
            self.__outputs = list(self.__outputs)
        return self.__outputs

    # @qt_core.Property("QVariantList", constant=True)
    # def outputsModel(self) -> list:
    #     return self.outputs

    @name.setter
    def __set_name(self, value: str):
        self.__name = value

    @qt_core.Property("quint64", constant=True)
    def balance(self) -> int:
        return self.__balance

    @balance.setter
    def __set_balance(self, value: int):
        self.__balance = value

    @qt_core.Property(str, constant=True)
    def unit(self) -> str:
        return self.__wallet._coin.unit

    @qt_core.Property(str, constant=True)
    def feeHuman(self) -> str:
        return str(self.__wallet._coin.balance_human(self.__fee))

    @qt_core.Property(str, constant=True)
    def fiatBalance(self) -> str:
        return str(self.__wallet._coin.fiat_amount(self.__balance))

    @qt_core.Property(str, constant=True)
    def timeHuman(self) -> str:
        return datetime.datetime.fromtimestamp(self.__time).strftime("%x %X")

    @qt_core.Property(str, notify=heightChanged)
    def block(self) -> str:
        "can be none"
        if self.__height is None:
            return "-"
        return str(self.__height)

    @qt_core.Property(int, notify=statusChanged)
    def status(self) -> int:
        # Pending, Unconfirmed, Confirmed, Complete
        """
        0 - Pending
        1 - Unconfirmed
        2 - Confirmed
        3 - Complete
        """
        if self.__local:
            return 0
        if self.__coin_base:
            return 3
        cc = self.confirmCount
        if cc >= self.READY_CONFIRM_COUNT:
            return 3
        if cc == 0:
            return 1
        return 2


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


class InputType(enum.IntFlag):
    """
    Keep it as flag for future use
    """
    INPUT = 0
    OUTPUT = 1


class Input:
    out = False
    __slots__ = ["amount", "address", "tx", "type"]

    def __init__(self, tx: Transaction):
        assert tx is not None
        self.tx = tx
        self.amount = None
        self.address = None
        self.type = ""

    @classmethod
    def from_dict(cls, table: dict, tx: Transaction):
        inp = cls(tx)
        inp.address = table["address"]
        inp.amount = table["amount"]
        inp.type = table["type"] or ''
        return inp

    def from_args(self, arg_iter: Iterable):
        """
                !! type has been eaten by tx !!
                {self.address_column},
                {self.amount_column},
                {self.output_type},
        """
        try:
            self.address = next(arg_iter)
            self.amount = next(arg_iter)
            self.type = next(arg_iter)
        except StopIteration:
            log.error(f"Too few arguments for Input {self}")

    @property
    def amountHuman(self) -> int:
        return self.tx.wallet.coin.balance_human(self.amount)

    def dump(self) -> dict:
        return {
            'address': self.address,
            'amount': self.amount,
        }

    def __str__(self) -> str:
        return f"IN: {self.address}:{self.amount}"


class Output(Input):
    out = True

    def __init__(self, tx: Transaction):
        super().__init__(tx=tx)

    def __str__(self) -> str:
        return f"OUT: {self.address}:{self.amount}"
