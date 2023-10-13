from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import QObject, Qt
from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as QSlot

from ....coins.abstract import Coin
from . import AbstractCoinStateModel, AbstractModel
from .abstract import (
    AbstractCoinObjectModel,
    AbstractSortFilterProxyModel,
    AbstractTableModel,
    QModelIndex
)
from .amount import AbstractAmountModel
from .tx import TxListModel

if TYPE_CHECKING:
    from typing import Final

    from .. import QmlApplication

_TX_NOTIFIED_LIST = []  # TODO tmp


class AbstractAddressStateModel(AbstractCoinStateModel):
    def __init__(
        self, application: QmlApplication, address: Coin.Address
    ) -> None:
        super().__init__(application, address.coin)
        self._address = address


class AbstractAddressBalanceModel(AbstractAmountModel):
    def __init__(
        self, application: QmlApplication, address: Coin.Address
    ) -> None:
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
        self, application: QmlApplication, address: Coin.Address
    ) -> None:
        super().__init__(application, address=address)

        self._balance_model = AddressBalanceModel(
            self._application, self._address
        )
        self.connectModelUpdate(self._balance_model)

        self._state_model = AddressStateModel(self._application, self._address)
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
        return self._registerList(
            TxListModel(self._application, self._address.txList, column_count)
        )

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
                "{tx_name}\n{amount} {unit} / {fiat_amount} {fiat_unit}"
            )
            text = text.format(
                tx_name=tx_model.nameHuman,
                amount=tx_model.amount.valueHuman,
                unit=tx_model.amount.unit,
                fiat_amount=tx_model.amount.fiatValueHuman,
                fiat_unit=tx_model.amount.fiatUnit,
            )

            self._application.showMessage(
                type_=self._application.MessageType.INFORMATION,
                title=title,
                text=text,
            )


class AddressListModel(AbstractTableModel):
    pass


class AddressListSortFilterProxyModel(AbstractSortFilterProxyModel):
    # TODO Sorting
    class FilterRole(AbstractSortFilterProxyModel.FilterRole):
        HideEmpty: Final = 1

    def __init__(
        self,
        application: QmlApplication,
        source_model: AbstractTableModel
    ) -> None:
        super().__init__(application, source_model)

    @QSlot(int)
    def setFilterRole(self, role: int) -> None:
        super().setFilterRole(role)

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QModelIndex
    ) -> bool:
        index = self.sourceModel().index(source_row, 0, source_parent)
        address = self.sourceModel().data(index, Qt.UserRole + 1)

        # TODO: store multiply filters
        if self.filterRole() == self.FilterRole.HideEmpty.value:
            return address.balance.value > 0
        return True

    def lessThan(
        self,
        source_left: QModelIndex,
        source_right: QModelIndex
    ) -> bool:
        pass
