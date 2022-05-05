from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (
    Property as QProperty,
    QObject,
    Signal as QSignal,
    Slot as QSlot)

from . import AbstractCoinStateModel, AbstractModel, ValidStatus
from .address import AddressListModel, AddressListSortedModel
from .amount import AbstractAmountModel
from .list import AbstractListModel, RoleEnum
from .tx import TxListConcatenateModel, TxListSortedModel
from ....coins.abstract import Coin

if TYPE_CHECKING:
    from .. import QmlApplication
    from ....currency import FiatRate


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

    def _getValue(self) -> int | None:
        return self._coin.balance


class CoinReceiveManagerModel(AbstractCoinStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: QmlApplication, coin: Coin) -> None:
        super().__init__(application, coin)
        self._address: Coin.Address | None = None

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


class CoinModel(Coin.Model, AbstractModel):
    def __init__(self, application: QmlApplication, coin: Coin) -> None:
        super().__init__(
            application,
            coin=coin,
            query_scheduler=application.networkQueryScheduler,
            database=application.database)

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

    @QProperty(QObject, constant=True)
    def txFactory(self) -> TxFactoryModel:
        return self._coin.txFactory.model

    def afterSetIsEnabled(self, value: bool) -> None:
        self._state_model.update()
        # noinspection PyUnresolvedReferences
        super().afterSetIsEnabled(value)

    def afterSetHeight(self, value: int) -> None:
        self._state_model.update()
        # noinspection PyUnresolvedReferences
        super().afterSetHeight(value)

    def afterSetFiatRate(self, value: FiatRate) -> None:
        self._balance_model.update()
        self._coin.txFactory.model.update()
        # noinspection PyUnresolvedReferences
        super().afterSetFiatRate(value)

    def afterUpdateBalance(self, value: int) -> None:
        self._balance_model.update()
        # noinspection PyUnresolvedReferences
        super().afterUpdateBalance(value)

    def afterUpdateUtxoList(self, value: None) -> None:
        self._coin.txFactory.model.update()
        super().afterUpdateUtxoList(value)

    def beforeAppendAddress(self, address: Coin.Address) -> None:
        self._address_list_model.lock(self._address_list_model.lockInsertRows())
        super().beforeAppendAddress(address)

    def afterAppendAddress(self, address: Coin.Address) -> None:
        self._address_list_model.unlock()
        # noinspection PyUnresolvedReferences
        self._tx_list_model.addSourceModel(address.model.txList)
        super().afterAppendAddress(address)

    def afterSetServerData(self, value: dict[str, ...]) -> None:
        self._server_data_model.update()
        # noinspection PyUnresolvedReferences
        super().afterSetServerData(value)


class CoinListModel(AbstractTableModel):
    pass
