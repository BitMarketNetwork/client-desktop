# JOK4
from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel, ValidStatus
from .address import \
    AddressListModel, \
    AddressListSortedModel
from .amount import AbstractAmountModel
from .list import \
    AbstractListModel, \
    RoleEnum
from .tx import \
    TxListConcatenateModel, \
    TxListSortedModel
from ..coin_interfaces import CoinInterface

if TYPE_CHECKING:
    from typing import Final, Optional
    from ..coins.abstract.coin import AbstractCoin
    from ..ui.gui import GuiApplication


class CoinStateModel(AbstractStateModel):
    __stateChanged = QSignal()

    @QProperty(bool, notify=__stateChanged)
    def enabled(self) -> bool:
        return self._coin.enabled

    @enabled.setter
    def _setEnabled(self, value: bool) -> None:
        self._coin.enabled = value


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


class CoinAmountModel(AbstractAmountModel):
    def refresh(self) -> None:
        super().refresh()
        for address in self._coin.addressList:
            address.model.amount.refresh()

    def _getValue(self) -> Optional[int]:
        return self._coin.amount


class CoinReceiveManagerModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: GuiApplication, coin: AbstractCoin) -> None:
        super().__init__(application, coin)
        self._address: Optional[AbstractCoin.Address] = None

    def _getValidStatus(self) -> ValidStatus:
        if self._address is not None:
            return ValidStatus.Reject
        return super()._getValidStatus()

    @QProperty(str, notify=__stateChanged)
    def name(self) -> str:
        return "" if self._address is None else self._address.name

    @QProperty(str, notify=__stateChanged)
    def label(self) -> str:
        return "" if self._address is None else self._address.label

    @QProperty(str, notify=__stateChanged)
    def comment(self) -> str:
        return "" if self._address is None else self._address.comment

    @QProperty(bool, notify=__stateChanged)
    def isSegwit(self) -> bool:
        return True if self._address is None else True  # TODO

    # noinspection PyTypeChecker
    @QSlot(bool, str, str, result=bool)
    def create(self, is_segwit: bool, label: str, comment: str) -> bool:
        if is_segwit:
            address_type = self._coin.Address.Type.WITNESS_V0_KEY_HASH
        else:
            address_type = self._coin.Address.Type.PUBKEY_HASH

        self._address = self._coin.deriveHdAddress(
            account=0,
            is_change=False,
            type_=address_type,
            label=label,
            comment=comment)
        if self._address is None:
            self.refresh()
            return False

        self._coin.appendAddress(self._address)
        self.refresh()
        return True

    @QSlot()
    def clear(self) -> None:
        self._address = None
        self.refresh()


class CoinManagerModel(AbstractStateModel):
    # noinspection PyTypeChecker
    @QSlot(bool, str, str, result=str)
    def createAddress(
            self,
            is_segwit: bool,
            label: str,
            comment: str) -> str:
        receive_manager = CoinReceiveManagerModel(
            self._application,
            self._coin)
        if receive_manager.create(is_segwit, label, comment):
            return receive_manager.name
        return ""

    # noinspection PyTypeChecker
    @QSlot(str, str, str, result=bool)
    def createWatchOnlyAddress(
            self,
            address_name: str,
            label: str,
            comment: str) -> bool:
        address = self._coin.Address.decode(
            self._coin,
            name=address_name,
            label=label,
            comment=comment)
        if address is None:
            return False
        self._coin.appendAddress(address)
        return True

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def isValidAddress(self, address_name: str) -> bool:
        if self._coin.Address.decode(self._coin, name=address_name) is None:
            return False
        return True


class CoinModel(CoinInterface, AbstractModel):
    def __init__(self, application: GuiApplication, coin: AbstractCoin) -> None:
        super().__init__(
            application,
            query_scheduler=application.networkQueryScheduler,
            database=application.database,
            coin=coin)

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

        self._receive_manager = CoinReceiveManagerModel(
            self._application,
            self._coin)
        self.connectModelRefresh(self._receive_manager)

        self._manager = CoinManagerModel(
            self._application,
            self._coin)
        self.connectModelRefresh(self._manager)

    @QProperty(str, constant=True)
    def name(self) -> str:
        return self._coin.name

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

    @QProperty(QObject, constant=True)
    def receiveManager(self) -> CoinReceiveManagerModel:
        return self._receive_manager

    @QProperty(QObject, constant=True)
    def manager(self) -> CoinManagerModel:
        return self._manager

    def afterSetEnabled(self) -> None:
        self._state_model.refresh()
        super().afterSetEnabled()

    def afterSetHeight(self) -> None:
        self._state_model.refresh()
        super().afterSetHeight()

    def afterSetStatus(self) -> None:
        super().afterSetStatus()

    def afterSetFiatRate(self) -> None:
        self._amount_model.refresh()
        self._coin.mutableTx.model.refresh()
        super().afterSetFiatRate()

    def afterRefreshAmount(self) -> None:
        self._amount_model.refresh()
        super().afterRefreshAmount()

    def afterRefreshUtxoList(self) -> None:
        self._coin.mutableTx.model.refresh()
        super().afterRefreshUtxoList()

    def beforeAppendAddress(self, address: AbstractCoin.Address) -> None:
        self._address_list_model.lock(self._address_list_model.lockInsertRows())
        super().beforeAppendAddress(address)

    def afterAppendAddress(self, address: AbstractCoin.Address) -> None:
        self._address_list_model.unlock()
        # noinspection PyUnresolvedReferences
        self._tx_list_model.addSourceModel(address.model.txList)
        super().afterAppendAddress(address)

    def afterSetServerData(self) -> None:
        self._server_data_model.refresh()
        super().afterSetServerData()


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
        MUTABLE_TX: Final = auto()
        RECEIVE_MANAGER: Final = auto()
        MANAGER: Final = auto()

    ROLE_MAP: Final = {
        Role.SHORT_NAME: (
            b"name",
            lambda c: c.model.name),
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
        Role.MUTABLE_TX: (
            b"mutableTx",
            lambda c: c.mutableTx.model),
        Role.RECEIVE_MANAGER: (
            b"receiveManager",
            lambda c: c.model.receiveManager),
        Role.MANAGER: (
            b"manager",
            lambda c: c.model.manager)
    }
