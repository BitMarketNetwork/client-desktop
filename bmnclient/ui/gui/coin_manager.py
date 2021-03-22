from __future__ import annotations
import logging
from typing import TYPE_CHECKING

import PySide2.QtCore as qt_core
from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal
from ...wallet import address, key, coins
from . import import_export
from ...models.coin import CoinListModel

if TYPE_CHECKING:
    from . import Application

log = logging.getLogger(__name__)


class CoinManager(QObject):
    coinIndexChanged = QSignal()
    addressIndexChanged = QSignal()
    emptyBalancesChanged = QSignal()

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application
        self.__current_coin_idx = -1
        self._coin_list_model = CoinListModel(self._application, self._application.coinList)

    @QProperty(qt_core.QObject, constant=True)
    def coinListModel(self) -> qt_core.QObject:
        return self._coin_list_model

    @QProperty(int, notify=coinIndexChanged)
    def coinIndex(self) -> int:
        return self.__current_coin_idx

    @QProperty(coins.CoinType, notify=coinIndexChanged)
    def coin(self) -> 'coins.CoinType':
        if self.__current_coin_idx >= 0:
            return self._application.coinList[self.__current_coin_idx]

    @coinIndex.setter
    def __set_coin_index(self, idx: int):
        if idx == self.__current_coin_idx:
            return
        assert idx < len(self._application.coinList)
        self.__current_coin_idx = idx
        self.update_tx_model()
        self.addressIndexChanged.emit()
        self.update_tx_model()
        # self.addressIndexChanged.emit()
        self.coinIndexChanged.emit()

    @QProperty(str, constant=True)
    def currency(self) -> str:
        return "USD"  # TODO

    @QProperty(qt_core.QObject, constant=True)
    def txModel(self) -> qt_core.QObject:
        return self.__tx_model

    def update_tx_model(self):
        self.__tx_model.address = self.address

    @qt_core.Slot()
    def getCoinUnspentList(self):
        if self.coin:
            # TODO: we shouldn't get unspents from read only addresses
            for addr in self.coin.addressList:  # pylint: disable=not-an-iterable
                if not addr.readOnly and addr.balance > 0:
                    self._application.networkThread.unspent_list(addr)
        else:
            log.warn("No current coin")

    @qt_core.Slot()
    def getAddressUnspentList(self):
        if self.address:
            self._application.networkThread.unspent_list(self.address)

    @qt_core.Slot(int, str, bool)
    def makeAddress(self, coin_index: int, label: str, segwit: bool):
        if coin_index >= 0:
            log.debug(f"Coin idx:{coin_index}")
            try:
                coin = self._application.coinList[coin_index]
                coin.make_address(
                    key.AddressType.P2WPKH if segwit else key.AddressType.P2PKH, label)
            except address.AddressError as ca:
                log.error(f"Can't make new address: {ca}")
        else:
            log.error(f"No coin selected {coin_index}!")

    @qt_core.Slot(str, str, result=bool)
    def isValidAddress(self, coin_short_name: str, address_name: str) -> bool:
        coin = self._application.findCoin(coin_short_name)
        if coin is None or coin.decodeAddress(name=address_name) is None:
            return False
        return True

    @qt_core.Slot(int, str, str)
    def addWatchAddress(self, coin_index: int, name: str, label: str) -> None:
        """
        no checks here !!!
        """
        if coin_index >= 0:
            log.debug(f"Coin idx:{coin_index}")
            coin = self._application.coinList[coin_index]
            coin.add_watch_address(name, label)
        else:
            log.error(f"No coin selected {coin_index}!")

    @qt_core.Slot(int)
    def clearTransactions(self, address_index: int):
        log.debug(f"clearing tx list of adress: {address_index}")
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self.__current_coin_idx} address:{address_index}")
            return
        addrss = self.coin(address_index)
        self.__tx_model.clear(addrss)
        self._application.databaseThread.clear_transactions(addrss)
        self.__tx_model.clear_complete(addrss)

    @qt_core.Slot(int)
    def removeAddress(self, address_index: int):
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self.__current_coin_idx} address:{address_index}")
            return
        log.debug(f"removing adress: {address_index}")
        self._application.databaseThread.delete_wallet(
            self.coin[address_index])  # pylint: disable=unsubscriptable-object
        self.__tx_model.clear(self.coin[address_index])

    @qt_core.Slot(int)
    def exportTransactions(self, address_index: int):
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self.__current_coin_idx} address:{address_index}")
            return
        iexport = import_export.ImportExportDialog()
        filename = iexport.doExport(
            self.tr("Select file to save transactions"), ".json")
        self.coin[address_index].export_txs(  # pylint: disable=unsubscriptable-object
            filename)

    @qt_core.Slot(int)
    def updateAddress(self, address_index: int):
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self.__current_coin_idx} address:{address_index}")
            return
        self._application.networkThread.updateAddress.emit(
            self.coin[address_index])  # pylint: disable=unsubscriptable-object

    def update_tx(self, tx_: 'tx.Transaction') -> None:
        if self.address == tx_.wallet:
            # TODO: !!! use tx
            self.__tx_model.update_confirm_count(3)

    def render_cell(self, coin):
        for c in self._application.coinList:
            if c is coin:
                self.renderCell.emit(c)
                return

    @qt_core.Slot(int)
    def increaseBalance(self, address_idx: int) -> int:
        add = self.coin(address_idx)
        add.balance += 1000000

    @qt_core.Slot(int)
    def reduceBalance(self, address_idx: int) -> int:
        add = self.coin(address_idx)
        add.balance *= 0.5

    @qt_core.Slot(int)
    def clearBalance(self, address_idx: int) -> int:
        add = self.coin(address_idx)
        add.balance = 0
