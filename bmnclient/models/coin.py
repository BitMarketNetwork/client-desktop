# JOK++
from __future__ import annotations

from enum import auto
from typing import Optional, TYPE_CHECKING

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
    TxListSortedModel
from ..coins.coin import CoinModelInterface
from ..ui.gui.tx_controller import TxController

if TYPE_CHECKING:
    from typing import Final
    from ..coins.address import AbstractAddress
    from ..coins.coin import AbstractCoin
    from ..ui.gui import Application


class CoinStateModel(AbstractStateModel):
    __stateChanged = QSignal()

    @QProperty(bool, notify=__stateChanged)
    def visible(self) -> bool:
        return self._coin.visible

    @visible.setter
    def _setVisible(self, value) -> None:
        self._coin.visible = value


class CoinServerDataModel(AbstractStateModel):
    __stateChanged = QSignal()

    @QProperty(str, notify=__stateChanged)
    def serverUrl(self) -> str:
        return self._coin.serverData.get("server_url", "-")

    @QProperty(str, notify=__stateChanged)
    def serverName(self) -> str:
        return self._coin.serverData.get("server_name", "-")

    @QProperty(int, notify=__stateChanged)
    def serverVersion(self) -> int:
        return self._coin.serverData.get("server_version", -1)

    @QProperty(str, notify=__stateChanged)
    def serverVersionHex(self) -> str:
        version = self.serverVersion
        # noinspection PyTypeChecker
        return "0x{:08x}".format(0 if version < 0 else version)

    @QProperty(str, notify=__stateChanged)
    def serverVersionHuman(self) -> str:
        return self._coin.serverData.get("server_version_string", "-")

    @QProperty(int, notify=__stateChanged)
    def version(self) -> int:
        return self._coin.serverData.get("version", -1)

    @QProperty(str, notify=__stateChanged)
    def versionHex(self) -> str:
        version = self.version
        # noinspection PyTypeChecker
        return "0x{:08x}".format(0 if version < 0 else version)

    @QProperty(str, notify=__stateChanged)
    def versionHuman(self) -> str:
        return self._coin.serverData.get("version_string", "-")

    @QProperty(int, notify=__stateChanged)
    def status(self) -> int:
        return self._coin.serverData.get("status", -1)

    @QProperty(int, notify=__stateChanged)
    def height(self) -> int:
        return self._coin.serverData.get("height", -1)

    @QProperty(str, notify=__stateChanged)
    def heightHuman(self) -> str:
        height = self.height
        # noinspection PyTypeChecker
        return "-" if height < 0 else self.locale.integerToString(height)


class CoinAmountModel(AmountModel):
    def refresh(self) -> None:
        super().refresh()
        for address in self._coin.addressList:
            address.model.amount.refresh()
        # TODO tmp
        self._coin.model.txController.model.amount.refresh()

    def _getValue(self) -> Optional[int]:
        return self._coin.amount


class CoinModel(CoinModelInterface, AbstractModel):
    def __init__(self, application: Application, coin: AbstractCoin) -> None:
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

        self._server_data_model = CoinServerDataModel(
            self._application,
            self._coin)
        self.connectModelRefresh(self._server_data_model)

        self._address_list_model = AddressListModel(
            self._application,
            self._coin.addressList)
        self._tx_list_model = TxListConcatenateModel(self._application)

        # TODO tmp
        self._tx_controller = TxController(
            self._application,
            self._coin)

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
    def serverData(self) -> CoinServerDataModel:
        return self._server_data_model

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
    def txList(self) -> TxListConcatenateModel:
        return self._tx_list_model

    # noinspection PyTypeChecker
    @QSlot(result=QObject)
    def txListSorted(self) -> TxListSortedModel:
        return TxListSortedModel(self._application, self._tx_list_model)

    # TODO tmp
    @QProperty(QObject, constant=True)
    def txController(self) -> TxController:
        return self._tx_controller

    def afterSetHeight(self) -> None:
        self._state_model.refresh()

    def afterSetStatus(self) -> None:
        pass

    def afterSetFiatRate(self) -> None:
        self._amount_model.refresh()

    def afterRefreshAmount(self) -> None:
        self._amount_model.refresh()

    def beforeAppendAddress(self, address: AbstractAddress) -> None:
        self._address_list_model.lock(self._address_list_model.lockInsertRows())

    def afterAppendAddress(self, address: AbstractAddress) -> None:
        self._address_list_model.unlock()
        # noinspection PyUnresolvedReferences
        self._tx_list_model.addSourceModel(address.model.txList)
        self._application.networkThread.update_wallet(address)  # TODO
        self._application.networkThread.unspent_list(address)  # TODO

    def afterSetServerData(self) -> None:
        self._server_data_model.refresh()


class CoinListModel(AbstractListModel):
    class Role(RoleEnum):
        SHORT_NAME: Final = auto()
        FULL_NAME: Final = auto()
        ICON_PATH: Final = auto()
        AMOUNT: Final = auto()
        STATE: Final = auto()
        SERVER_DATA: Final = auto()
        ADDRESS_LIST: Final = auto()
        TX_LIST: Final = auto()
        TX_CONTROLLER: Final = auto()

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
        Role.SERVER_DATA: (
            b"serverData",
            lambda c: c.model.serverData),
        Role.ADDRESS_LIST: (
            b"addressList",
            lambda c: c.model.addressListSorted()),
        Role.TX_LIST: (
            b"txList",
            lambda c: c.model.txListSorted()),
        Role.TX_CONTROLLER: (
            b"txController",
            lambda c: c.model.txController.model)
    }
