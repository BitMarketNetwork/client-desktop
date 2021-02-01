# JOK++
from __future__ import annotations

from enum import IntEnum
from functools import lru_cache
from typing import Any, List, Optional, Sequence, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QAbstractListModel, \
    QByteArray, \
    QModelIndex, \
    QObject, \
    QSortFilterProxyModel, \
    Qt, \
    Signal as QSignal

if TYPE_CHECKING:
    from ..wallet.address import CAddress
    from ..wallet.coins import CoinType
    from ..wallet.tx import Transaction
    from ..ui.gui import Application


class RoleEnum(IntEnum):
    def _generate_next_value_(
            self,
            start: int,
            count: int,
            last_values: List[int]) -> int:
        return Qt.UserRole + count


class AbstractListModel(QAbstractListModel):
    class LockInsertRow:
        def __init__(self, owner: AbstractListModel, index: int):
            self._owner = owner
            self._index = index

        def __enter__(self) -> None:
            self._owner.beginInsertRows(QModelIndex(), self._index, self._index)

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            self._owner.endInsertRows()

    class LockRemoveRow:
        def __init__(self, owner: AbstractListModel, index: int):
            self._owner = owner
            self._index = index

        def __enter__(self) -> None:
            self._owner.beginRemoveRows(QModelIndex(), self._index, self._index)

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            self._owner.endRemoveRows()

    _ROLE_MAP = {}

    def __init__(self, source_list: Sequence) -> None:
        super().__init__()
        self._source_list = source_list

    @lru_cache()
    def roleNames(self) -> dict:
        return {k: QByteArray(v[0]) for (k, v) in self._ROLE_MAP.items()}

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._source_list)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        if not 0 <= index.row() < self.rowCount() or not index.isValid():
            return None
        return self._ROLE_MAP[role][1](self._source_list[index.row()])

    def lockInsertRow(self, index: Optional[int] = None) -> LockInsertRow:
        return self.LockInsertRow(
            self,
            self.rowCount() if index is None else index)

    def lockRemoveRow(self, index) -> LockRemoveRow:
        return self.LockRemoveRow(self, index)


class AbstractListSortedModel(QSortFilterProxyModel):
    def __init__(self, source_model: AbstractListModel, sort_role: int) -> None:
        super().__init__()
        self.setSourceModel(source_model)
        self.setSortRole(sort_role)
        self.sort(0, Qt.AscendingOrder)


class AbstractCoinStateModel(QObject):
    _stateChanged: Optional[QSignal] = None

    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__()
        self._application = application
        self._coin = coin

    def refresh(self) -> None:
        if self._stateChanged:
            self._stateChanged.emit()


class AbstractAddressStateModel(AbstractCoinStateModel):
    def __init__(self, application: Application, address: CAddress) -> None:
        super().__init__(application, address.coin)
        self._address = address


class AbstractTxStateModel(AbstractAddressStateModel):
    def __init__(self, application: Application, tx: Transaction) -> None:
        super().__init__(application, tx.wallet)
        self._tx = tx


class AbstractAmountModel:
    _stateChanged = QSignal()

    def _value(self) -> int:
        raise NotImplementedError

    def _fiatValue(self) -> float:
        raise NotImplementedError

    @QProperty(str, notify=_stateChanged)
    def value(self) -> int:
        return self._value()

    @QProperty(str, notify=_stateChanged)
    def valueHuman(self) -> str:
        # noinspection PyUnresolvedReferences
        return self._coin.amountToString(
            self._value(),
            locale=self._application.language.locale)

    @QProperty(str, constant=True)
    def unit(self) -> str:
        # noinspection PyUnresolvedReferences
        return self._coin.unit

    @QProperty(str, notify=_stateChanged)
    def fiatValueHuman(self) -> str:
        # noinspection PyUnresolvedReferences
        return self._application.language.locale.floatToString(
            self._fiatValue(),
            2)

    @QProperty(str, notify=_stateChanged)
    def fiatUnit(self) -> str:
        return "USD"  # TODO
