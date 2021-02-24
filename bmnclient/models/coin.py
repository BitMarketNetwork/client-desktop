# JOK++
from __future__ import annotations

from enum import auto
from typing import Final, Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel
from .address import \
    AddressListModel, \
    AddressListSortedModel
from .amount import AmountModel
from .list import \
    AbstractListModel, \
    RoleEnum
from .tx import \
    TxListConcatenateModel, \
    TxListModel, \
    TxListSortedModel
from ..coins.coin import CoinModelInterface
from ..wallet.address import CAddress

if TYPE_CHECKING:
    from ..wallet.coins import CoinType
    from ..ui.gui import Application


class CoinStateModel(AbstractStateModel):
    __stateChanged = QSignal()

    @QProperty(bool, notify=__stateChanged)
    def visible(self) -> bool:
        return self._coin.visible

    @visible.setter
    def _setVisible(self, value) -> None:
        self._coin.visible = value


class CoinRemoteStateModel(AbstractStateModel):
    __stateChanged = QSignal()

    @QProperty(str, notify=__stateChanged)
    def versionHuman(self) -> str:
        # noinspection PyProtectedMember
        return self._coin._remote.get("version_string", "-")  # TODO

    @QProperty(int, notify=__stateChanged)
    def version(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("version", -1)  # TODO

    @QProperty(int, notify=__stateChanged)
    def status(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("status", -1)  # TODO

    @QProperty(int, notify=__stateChanged)
    def height(self) -> int:
        # noinspection PyProtectedMember
        return self._coin._remote.get("height", -1)  # TODO

    @QProperty(str, notify=__stateChanged)
    def heightHuman(self) -> str:
        height = self.height
        if height < 0:
            return "-"
        return self.locale.integerToString(height)


class CoinAmountModel(AmountModel):
    def _getValue(self) -> Optional[int]:
        return self._coin.amount


class CoinModel(CoinModelInterface, AbstractModel):
    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__(application)
        self._coin = coin

        self._amount_model = CoinAmountModel(
            self._application,
            self._coin)
        self.connectModelRefresh(self._amount_model)

        self._state_model = CoinStateModel(
            self._application,
            self._coin)
        self.connectModelRefresh(self._state_model)

        self._remote_state_model = CoinRemoteStateModel(
            self._application,
            self._coin)
        self.connectModelRefresh(self._remote_state_model)

        self._address_list_model = AddressListModel(
            self._application,
            self._coin.addressList)
        self._tx_list_model = TxListConcatenateModel(self._application)

    @QProperty(str, constant=True)
    def shortName(self) -> str:
        return self._coin.shortName

    @QProperty(str, constant=True)
    def fullName(self) -> str:
        return self._coin.fullName

    @QProperty(str, constant=True)
    def iconPath(self) -> str:
        return self._coin.iconPath

    @QProperty(QObject, constant=True)
    def amount(self) -> CoinAmountModel:
        return self._amount_model

    @QProperty(QObject, constant=True)
    def state(self) -> CoinStateModel:
        return self._state_model

    @QProperty(QObject, constant=True)
    def remoteState(self) -> CoinRemoteStateModel:
        return self._remote_state_model

    @QProperty(QObject, constant=True)
    def addressList(self) -> AddressListModel:
        return self._address_list_model

    # noinspection PyTypeChecker
    @QSlot(result=QObject)
    def addressListSorted(self) -> AddressListSortedModel:
        return AddressListSortedModel(
            self._application,
            self._address_list_model)

    @QProperty(QObject, constant=True)
    def txList(self) -> TxListModel:
        return self._tx_list_model

    # noinspection PyTypeChecker
    @QSlot(result=QObject)
    def txListSorted(self) -> TxListSortedModel:
        return TxListSortedModel(self._application, self._tx_list_model)

    def beforeAppendAddress(self, address: CAddress) -> None:
        self._address_list_model.lock(self._address_list_model.lockInsertRows())

    def afterAppendAddress(self, address: CAddress) -> None:
        self._address_list_model.unlock()
        # noinspection PyUnresolvedReferences
        self._tx_list_model.addSourceModel(address.model.txList)
        self._application.networkThread.update_wallet(address)  # TODO

    def afterRefreshAmount(self) -> None:
        self._amount_model.refresh()

    def afterSetFiatRate(self) -> None:
        self._amount_model.refresh()


class CoinListModel(AbstractListModel):
    class Role(RoleEnum):
        SHORT_NAME: Final = auto()
        FULL_NAME: Final = auto()
        ICON_PATH: Final = auto()
        AMOUNT: Final = auto()
        STATE: Final = auto()
        REMOTE_STATE: Final = auto()
        ADDRESS_LIST: Final = auto()
        TX_LIST: Final = auto()

    ROLE_MAP: Final = {
        Role.SHORT_NAME: (
            b"shortName",
            lambda c: c.model.shortName),
        Role.FULL_NAME: (
            b"fullName",
            lambda c: c.model.fullName),
        Role.ICON_PATH: (
            b"iconPath",
            lambda c: c.model.iconPath),
        Role.AMOUNT: (
            b"amount",
            lambda c: c.model.amount),
        Role.STATE: (
            b"state",
            lambda c: c.model.state),
        Role.REMOTE_STATE: (
            b"remoteState",
            lambda c: c.model.remoteState),
        Role.ADDRESS_LIST: (
            b"addressList",
            lambda c: c.model.addressListSorted()),
        Role.TX_LIST: (
            b"txList",
            lambda c: c.model.txListSorted())
    }
