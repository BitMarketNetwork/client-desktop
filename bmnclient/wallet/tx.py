from __future__ import annotations

import datetime
import logging
from typing import Iterable, List, Optional

import PySide2.QtCore as qt_core

from . import db_entry
from .address import CAddress
from ..coins.tx import AbstractTx

log = logging.getLogger(__name__)


class TxError(Exception):
    pass


class Transaction(db_entry.DbEntry, AbstractTx):
    READY_CONFIRM_COUNT = 6
    statusChanged = qt_core.Signal()
    # constant fields can be changed while reprocessing
    infoChanged = qt_core.Signal()

    def __init__(self, address: CAddress):
        super().__init__()
        AbstractTx.__init__(self, address=address)

        self.__coin_base = False
        self.__local = False

    def from_args(self, arg_iter: iter):
        try:
            self._rowid = next(arg_iter)
            self.__name = next(arg_iter)
            self._set_object_name(self.__name)
            assert isinstance(self.__name, str)
            self._height = next(arg_iter)
            self.__time = next(arg_iter)
            self.__balance = next(arg_iter)
            self.__fee = next(arg_iter)
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

        for item in body["input"]:
            item = Input.from_dict(item, self)
            a = CAddress(item.address, self._address.coin)
            a.balance = item.amount
            self.appendInput(a)

        for item in body["output"]:
            item = Output.from_dict(item, self)
            a = CAddress(item.address, self._address.coin)
            a.balance = item.amount
            self.appendOutput(a)

        return self

    def make_input(self, args: iter):
        if next(args):
            inp = Output(self)
            inp.from_args(args)
            a = CAddress(inp.address, coin=self._address.coin)
            a.balance = inp.amount
            self.appendOutput(a)
        else:
            inp = Input(self)
            inp.from_args(args)
            a = CAddress(inp.address, coin=self._address.coin)
            a.balance = inp.amount
            self.appendInput(a)

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
        cc = self.confirmations
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
