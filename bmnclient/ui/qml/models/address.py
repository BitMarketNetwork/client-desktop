from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QObject,
    Signal as QSignal,
    Slot as QSlot)

from . import AbstractCoinStateModel, AbstractModel
from .abstract import AbstractCoinObjectModel, AbstractTableModel
from .amount import AbstractAmountModel
from .tx import TxListModel
from ....coins.abstract import Coin

if TYPE_CHECKING:
    from .. import QmlApplication

_TX_NOTIFIED_LIST = []  # TODO tmp


class AbstractAddressStateModel(AbstractCoinStateModel):
    def __init__(
            self,
            application: QmlApplication,
            address: Coin.Address) -> None:
        super().__init__(application, address.coin)
        self._address = address


class AbstractAddressBalanceModel(AbstractAmountModel):
    def __init__(
            self,
            application: QmlApplication,
            address: Coin.Address) -> None:
        super().__init__(application, address.coin)
        self._address = address

    def _getValue(self) -> int | None:
        raise NotImplementedError


class AddressStateModel(AbstractAddressStateModel):
    __stateChanged = QSignal()

    @QProperty(int, notify=__stateChanged)
    def txCount(self) -> int:
        return self._address.txCount

    @QProperty(str, notify=__stateChanged)
    def label(self) -> str:
        return self._address.label

    @QProperty(bool, constant=True)
    def isReadOnly(self) -> bool:
        return self._address.isReadOnly

    @QProperty(bool, notify=__stateChanged)
    def isUpdating(self) -> bool:
        return False  # TODO self._address.isUpdating


class AddressBalanceModel(AbstractAddressBalanceModel):
    def _getValue(self) -> int | None:
        return self._address.balance


class AddressModel(AbstractCoinObjectModel, Coin.Address.Model, AbstractModel):
    def __init__(
            self,
            application: QmlApplication,
            address: Coin.Address) -> None:
        super().__init__(application, address=address)

        self._balance_model = AddressBalanceModel(
            self._application,
            self._address)
        self.connectModelUpdate(self._balance_model)

        self._state_model = AddressStateModel(
            self._application,
            self._address)
        self.connectModelUpdate(self._state_model)

    @QProperty(str, constant=True)
    def name(self) -> str:
        return self._address.name

    @QProperty(QObject, constant=True)
    def balance(self) -> AddressBalanceModel:
        return self._balance_model

    @QProperty(QObject, constant=True)
    def state(self) -> AddressStateModel:
        return self._state_model

    # noinspection PyTypeChecker
    @QSlot(int, result=QObject)
    def openTxList(self, column_count: int) -> TxListModel:
        return self._registerList(TxListModel(
            self._application,
            self._address.txList,
            column_count))

    def afterSetBalance(self, value: int) -> None:
        self._balance_model.update()
        super().afterSetBalance(value)

    def afterSetLabel(self, value: str) -> None:
        self._state_model.update()
        super().afterSetLabel(value)

    def afterSetComment(self, value: str) -> None:
        self._state_model.update()
        super().afterSetComment(value)

    def afterAppendTx(self, tx: Coin.Tx) -> None:  # TODO
        global _TX_NOTIFIED_LIST

        if tx.rowId is None and tx.name not in _TX_NOTIFIED_LIST:
            _TX_NOTIFIED_LIST.append(tx.name)
            tx_model = tx.model

            title = QObject().tr("New {coin_name} transaction")
            title = title.format(coin_name=tx.coin.fullName)

            text = QObject().tr(
                "{tx_name}\n{amount} {unit} / {fiat_amount} {fiat_unit}")
            text = text.format(
                tx_name=tx_model.nameHuman,
                amount=tx_model.amount.valueHuman,
                unit=tx_model.amount.unit,
                fiat_amount=tx_model.amount.fiatValueHuman,
                fiat_unit=tx_model.amount.fiatUnit)

            self._application.showMessage(
                type_=self._application.MessageType.INFORMATION,
                title=title,
                text=text)


class AddressListModel(AbstractTableModel):
    pass
