
import enum
import logging

import PySide2.QtCore as qt_core  # pylint: disable=import-error
from .model_shared import IntEnum, ba
log = logging.getLogger(__name__)


class Role(IntEnum):
    ADDRESS_ROLE = enum.auto()
    BALANCE_ROLE = enum.auto()
    TYPE_ROLE = enum.auto()


class InputModel(qt_core.QAbstractListModel):
    SELECTOR = {
        Role.ADDRESS_ROLE: lambda inp: inp.address,
        Role.BALANCE_ROLE: lambda inp: inp.amountHuman,
        Role.TYPE_ROLE: lambda inp: inp.type,
    }

    def __init__(self, tx_, input_type: bool):
        super().__init__(parent=tx_)
        self.tx_ = tx_
        self.__input_type = input_type

    def rowCount(self, parent=qt_core.QModelIndex()):
        return self.tx_.size(self.__input_type)

    def data(self, index, role=qt_core.Qt.DisplayRole):
        if 0 <= index.row() < self.rowCount() and index.isValid():
            try:
                return self.SELECTOR[role](self.tx_.get(index.row(), self.__input_type))
            except KeyError as ke:
                log.critical(f"{ke} ==> role:{role} row:{index.row()}")

    def roleNames(self) -> dict:
        return {
            Role.ADDRESS_ROLE: ba(b"addressName"),
            Role.BALANCE_ROLE: ba(b"amountHuman"),
            Role.TYPE_ROLE: ba(b"type"),
        }
