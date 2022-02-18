from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from PySide6.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractCoinStateModel, AbstractModel, ValidStatus
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
from ....coin_interfaces import CoinInterface

if TYPE_CHECKING:
    from typing import Final, Optional
    from .. import QmlApplication
    from ....coins.abstract import Coin


class CoinStateModel(AbstractCoinStateModel):
    __stateChanged = QSignal()

    @QProperty(bool, notify=__stateChanged)
    def isEnabled(self) -> bool:
        return self._coin.isEnabled

    @isEnabled.setter
    def isEnabled(self, value: bool) -> None:
        self._coin.isEnabled = value


class CoinServerDataModel(AbstractCoinStateModel):
    __stateChanged = QSignal()

    def _serverDataString(self, name: str) -> str:
        value = self._coin.serverData.get(name)
        return str(value) if value else self._NONE_STRING

    def _serverDataInteger(self, name: str) -> int:
        value = self._coin.serverData.get(name)
        return value if isinstance(value, int) else -1

    @QProperty(str, notify=__stateChanged)
    def serverUrl(self) -> str:
        return self._serverDataString("server_url")

    @QProperty(str, notify=__stateChanged)
    def serverName(self) -> str:
        return self._serverDataString("server_name")

    @QProperty(int, notify=__stateChanged)
    def serverVersion(self) -> int:
        return self._serverDataInteger("server_version")

    @QProperty(str, notify=__stateChanged)
    def serverVersionHex(self) -> str:
        version = self.serverVersion
        # noinspection PyTypeChecker
        return "0x{:08x}".format(0 if version < 0 else version)

    @QProperty(str, notify=__stateChanged)
    def serverVersionHuman(self) -> str:
        return self._serverDataString("server_version_string")

    @QProperty(int, notify=__stateChanged)
    def version(self) -> int:
        return self._serverDataInteger("version")

    @QProperty(str, notify=__stateChanged)
    def versionHex(self) -> str:
        version = self._serverDataInteger("version")
        return "0x{:08x}".format(0 if version < 0 else version)

    @QProperty(str, notify=__stateChanged)
    def versionHuman(self) -> str:
        return self._serverDataString("version_string")

    @QProperty(int, notify=__stateChanged)
    def status(self) -> int:
        return self._serverDataInteger("status")

    @QProperty(int, notify=__stateChanged)
    def height(self) -> int:
        return self._serverDataInteger("height")

    @QProperty(str, notify=__stateChanged)
    def heightHuman(self) -> str:
        height = self._serverDataInteger("height")
        if height < 0:
            return self._NONE_STRING
        return self.locale.integerToString(height)


class CoinBalanceModel(AbstractAmountModel):
    def update(self) -> None:
        super().update()
        for address in self._coin.addressList:
            address.model.balance.update()

    def _getValue(self) -> Optional[int]:
        return self._coin.balance


class CoinReceiveManagerModel(AbstractCoinStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: QmlApplication, coin: Coin) -> None:
        super().__init__(application, coin)
        self._address: Optional[Coin.Address] = None

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
    def isWitness(self) -> bool:
        return self._address is None  # TODO

    # noinspection PyTypeChecker
    @QSlot(bool, str, str, result=bool)
    def create(self, is_witness: bool, label: str, comment: str) -> bool:
        if is_witness:
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
            self.update()
            return False

        self._coin.appendAddress(self._address)
        self.update()
        return True

    @QSlot()
    def clear(self) -> None:
        self._address = None
        self.update()


class CoinManagerModel(AbstractCoinStateModel):
    # noinspection PyTypeChecker
    @QSlot(bool, str, str, result=str)
    def createAddress(
            self,
            is_witness: bool,
            label: str,
            comment: str) -> str:
        receive_manager = CoinReceiveManagerModel(
            self._application,
            self._coin)
        if receive_manager.create(is_witness, label, comment):
            return receive_manager.name
        return ""

    # noinspection PyTypeChecker
    @QSlot(str, str, str, result=bool)
    def createWatchOnlyAddress(
            self,
            address_name: str,
            label: str,
            comment: str) -> bool:
        address = self._coin.Address.createFromName(
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
        if not self._coin.Address.createFromName(self._coin, name=address_name):
            return False
        return True


class CoinModel(CoinInterface, AbstractModel):
    def __init__(self, application: QmlApplication, coin: Coin) -> None:
        super().__init__(
            application,
            query_scheduler=application.networkQueryScheduler,
            database=application.database,
            coin=coin)

        self._balance_model = CoinBalanceModel(
            self._application,
            self._coin)
        self.connectModelUpdate(self._balance_model)

        self._state_model = CoinStateModel(
            self._application,
            self._coin)
        self.connectModelUpdate(self._state_model)

        self._server_data_model = CoinServerDataModel(
            self._application,
            self._coin)
        self.connectModelUpdate(self._server_data_model)

        self._address_list_model = AddressListModel(
            self._application,
            self._coin.addressList)
        self._tx_list_model = TxListConcatenateModel(self._application)

        self._receive_manager = CoinReceiveManagerModel(
            self._application,
            self._coin)
        self.connectModelUpdate(self._receive_manager)

        self._manager = CoinManagerModel(
            self._application,
            self._coin)
        self.connectModelUpdate(self._manager)

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
    def balance(self) -> CoinBalanceModel:
        return self._balance_model

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
        self._state_model.update()
        super().afterSetEnabled()

    def afterSetHeight(self) -> None:
        self._state_model.update()
        super().afterSetHeight()

    def afterSetStatus(self) -> None:
        super().afterSetStatus()

    def afterSetFiatRate(self) -> None:
        self._balance_model.update()
        self._coin.txFactory.model.update()
        super().afterSetFiatRate()

    def afterUpdateBalance(self) -> None:
        self._balance_model.update()
        super().afterUpdateBalance()

    def afterUpdateUtxoList(self) -> None:
        self._coin.txFactory.model.update()
        super().afterUpdateUtxoList()

    def beforeAppendAddress(self, address: Coin.Address) -> None:
        self._address_list_model.lock(self._address_list_model.lockInsertRows())
        super().beforeAppendAddress(address)

    def afterAppendAddress(self, address: Coin.Address) -> None:
        self._address_list_model.unlock()
        # noinspection PyUnresolvedReferences
        self._tx_list_model.addSourceModel(address.model.txList)
        super().afterAppendAddress(address)

    def afterSetServerData(self) -> None:
        self._server_data_model.update()
        super().afterSetServerData()


class CoinListModel(AbstractListModel):
    class Role(RoleEnum):
        SHORT_NAME: Final = auto()
        FULL_NAME: Final = auto()
        ICON_PATH: Final = auto()
        BALANCE: Final = auto()
        STATE: Final = auto()
        SERVER_DATA: Final = auto()
        ADDRESS_LIST: Final = auto()
        TX_LIST: Final = auto()
        TX_FACTORY: Final = auto()
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
        Role.BALANCE: (
            b"balance",
            lambda c: c.model.balance),
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
        Role.TX_FACTORY: (
            b"txFactory",
            lambda c: c.txFactory.model),
        Role.RECEIVE_MANAGER: (
            b"receiveManager",
            lambda c: c.model.receiveManager),
        Role.MANAGER: (
            b"manager",
            lambda c: c.model.manager)
    }
