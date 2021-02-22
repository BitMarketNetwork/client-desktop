from __future__ import annotations

import datetime
import logging
from typing import Iterable, List, Optional

import PySide2.QtCore as qt_core

from . import db_entry, serialization
from .address import CAddress
from ..models.tx import \
    TransactionAmountModel, \
    TransactionFeeAmountModel, \
    TransactionIoListModel, \
    TransactionStateModel

log = logging.getLogger(__name__)


class TxError(Exception):
    pass


class TransactionIo(CAddress):
    pass


class Transaction(db_entry.DbEntry, serialization.SerializeMixin):
    READY_CONFIRM_COUNT = 6
    statusChanged = qt_core.Signal()
    # constant fields can be changed while reprocessing
    infoChanged = qt_core.Signal()
    heightChanged = qt_core.Signal()

    def __init__(self, wallet: CAddress):
        super().__init__()
        self._address = wallet
        self._input_list: List[TransactionIo] = []
        self._output_list: List[TransactionIo] = []
        self.__coin_base = False
        self.__height = 0
        self.__local = False

        from ..ui.gui import Application
        self._amount_model = TransactionAmountModel(Application.instance(), self)
        self._amount_model.moveToThread(Application.instance().thread())
        self._fee_amount_model = TransactionFeeAmountModel(Application.instance(), self)
        self._fee_amount_model.moveToThread(Application.instance().thread())
        self._state_model = TransactionStateModel(Application.instance(), self)
        self._state_model.moveToThread(Application.instance().thread())
        self._input_list_model = TransactionIoListModel(Application.instance(), self._input_list)
        self._input_list_model.moveToThread(Application.instance().thread())
        self._output_list_model = TransactionIoListModel(Application.instance(), self._output_list)
        self._output_list_model.moveToThread(Application.instance().thread())

    @property
    def amountModel(self) -> TransactionAmountModel:
        return self._amount_model

    @property
    def feeAmountModel(self) -> TransactionFeeAmountModel:
        return self._fee_amount_model

    @property
    def stateModel(self) -> TransactionStateModel:
        return self._state_model

    @property
    def inputListModel(self) -> TransactionIoListModel:
        return self._input_list_model

    @property
    def outputListModel(self) -> TransactionIoListModel:
        return self._output_list_model

    @classmethod
    def make_dummy(cls, wallet: Optional[CAddress]) -> Transaction:
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

            with self._input_list_model.lockReset():
                self._input_list.clear()
            with self._output_list_model.lockReset():
                self._output_list.clear()
        except StopIteration:
            log.error("Too few arguments for TX {self}")

    def parse(self, name: str, body: dict):
        self.__name = name
        self._set_object_name(name)
        self.__height = body.get("height", 0)
        self.__time = body["time"]
        self.__balance = body["amount"]
        self.__fee = body["fee"]
        self.__coin_base = body["coinbase"] != 0

        with self._input_list_model.lockReset():
            self._input_list.clear()
            for item in body["input"]:
                item = Input.from_dict(item, self)
                a = TransactionIo(item.address)
                a.moveToThread(self.thread())
                a.coin = self._address.coin
                a.balance = item.amount
                self._input_list.append(a)

        with self._output_list_model.lockReset():
            for item in body["output"]:
                item = Output.from_dict(item, self)
                a = TransactionIo(item.address)
                a.moveToThread(self.thread())
                a.coin = self._address.coin
                a.balance = item.amount
                self._output_list.append(a)

        return self

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
            with self._output_list_model.lockInsertRows():
                inp.from_args(args)
                a = TransactionIo(inp.address)
                a.coin = self._address.coin
                a.balance = inp.amount
                self._output_list.append(a)
        else:
            inp = Input(self)
            with self._input_list_model.lockInsertRows():
                inp.from_args(args)
                a = TransactionIo(inp.address)
                a.coin = self._address.coin
                a.balance = inp.amount
                self._input_list.append(a)

    @property
    def wallet(self) -> CAddress:
        return self._address

    @property
    def local(self) -> bool:
        return self.__local

    @local.setter
    def local(self, on: bool) -> None:
        self.__local = on

    @wallet.setter
    def wallet(self, wall: CAddress):
        self._address = wall
        if wall:
            self._address.heightChanged.connect(
                self.heightChanged, qt_core.Qt.QueuedConnection)
        # self.setParent(wall)

    @property
    def coin_base(self) -> int:
        return 1 if self.__coin_base else 0

    @qt_core.Property(int, notify=heightChanged)
    def confirmCount(self) -> int:
        if self.__height is not None \
                and self._address.coin.height:
            return max(0, self._address.coin.height - self.__height + 1)
        log.debug(
            f"no confirm: height:{self.__height} => {self._address.coin.height}")
        return 0

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
        self._state_model.refresh()

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
                                                               self._address.coin.currency.unit)

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
        return self._input_list

    @property
    def outputs(self) -> list:
        return self._output_list

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
        return self._address.coin.currency.unit

    @qt_core.Property(int, constant=True)
    def feeFiatBalance(self) -> int:
        return self._address.coin.fiat_amount(self.__fee)

    @qt_core.Property(str, constant=True)
    def timeHuman(self) -> str:
        return datetime.datetime.fromtimestamp(self.__time).strftime("%x %X")

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

    def __str__(self) -> str:
        return f"IN: {self.address}:{self.amount}"


class Output(Input):
    out = True

    def __init__(self, tx: Transaction):
        super().__init__(tx=tx)

    def __str__(self) -> str:
        return f"OUT: {self.address}:{self.amount}"
