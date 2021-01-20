
import enum

import PySide2.QtCore as qt_core  # pylint: disable=import-error
from .model_shared import IntEnum, ba
from ..wallet import coins


class Role(IntEnum):
    NAME_ROLE = enum.auto()
    ICON_ROLE = enum.auto()
    BALANCE_ROLE = enum.auto()
    FIAT_BALANCE_ROLE = enum.auto()
    UNIT_ROLE = enum.auto()
    TEST_ROLE = enum.auto()
    VISIBLE_ROLE = enum.auto()
    ENABLED_ROLE = enum.auto()
    ADDRESS_MODEL_ROLE = enum.auto()


class CoinModel(qt_core.QAbstractListModel):
    SELECTOR = {
        Role.NAME_ROLE: lambda coin_: coin_.fullName,
        Role.ICON_ROLE: lambda coin_: coin_.icon,
        Role.BALANCE_ROLE: lambda coin_: coin_.balance,
        Role.FIAT_BALANCE_ROLE: lambda coin_: coin_.fiatBalance,
        Role.UNIT_ROLE: lambda coin_: coin_.unit,
        Role.TEST_ROLE: lambda coin_: coin_.test,
        Role.VISIBLE_ROLE: lambda coin_: coin_.visible,
        Role.ENABLED_ROLE: lambda coin_: coin_.enabled,
        Role.ADDRESS_MODEL_ROLE: lambda coin_: coin_.addressModel,
    }

    def __init__(self, parent):
        super().__init__(parent=parent)
        # import pdb;pdb.set_trace()
        self.__mapper = qt_core.QSignalMapper(self)
        from ..application import CoreApplication
        for i, c in enumerate(CoreApplication.instance().coinList):
            c.balanceChanged.connect(self.__mapper.map)
            self.__mapper.setMapping(c, i)
        self.__mapper.mapped.connect(self.balance_changed)
        self.__show_empty_addresses = True

    def rowCount(self, parent=qt_core.QModelIndex()) -> int:
        from ..application import CoreApplication
        return len(CoreApplication.instance().coinList)

    def data(self, index, role=qt_core.Qt.DisplayRole):
        if 0 <= index.row() < self.rowCount() and index.isValid():
            from ..application import CoreApplication
            return self.SELECTOR[role](
                CoreApplication.instance().coinList[index.row()])

    def roleNames(self) -> dict:
        return {
            Role.NAME_ROLE: ba(b"fullName"),
            Role.ICON_ROLE: ba(b"icon"),
            Role.BALANCE_ROLE: ba(b"balance"),
            Role.FIAT_BALANCE_ROLE: ba(b"fiatBalance"),
            Role.UNIT_ROLE: ba(b"unit"),
            Role.TEST_ROLE: ba(b"test"),
            Role.VISIBLE_ROLE: ba(b"visible"),
            Role.ENABLED_ROLE: ba(b"enabled"),
            Role.ADDRESS_MODEL_ROLE: ba(b"addressModel"),
        }

    def balance_changed(self, index: int) -> None:
        self.dataChanged.emit(self.index(
            index), self.index(index), [Role.BALANCE_ROLE, Role.FIAT_BALANCE_ROLE])

    # TODO: it's not the right way.. you should implement proxy instead
    def reset(self) -> None:
        self.beginResetModel()

    def reset_complete(self) -> None:
        self.endResetModel()

    @property
    def show_empty_addresses(self) -> bool:
        return self.__show_empty_addresses

    @show_empty_addresses.setter
    def show_empty_addresses(self, value: bool) -> None:
        self.__show_empty_addresses = value

    @qt_core.Slot(int, result=coins.CoinType)
    def get(self, index: int) -> "coins.CoinType":
        from ..application import CoreApplication
        return CoreApplication.instance().coinList[index]
