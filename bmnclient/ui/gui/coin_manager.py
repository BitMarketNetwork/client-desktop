from __future__ import annotations
import logging
from typing import TYPE_CHECKING

import PySide2.QtCore as qt_core
from PySide2.QtCore import \
    QObject, \
    Signal as QSignal
from ...wallet import address, coin_model, key, tx, tx_model, coins
from . import import_export

if TYPE_CHECKING:
    from . import Application

log = logging.getLogger(__name__)


class CoinManager(QObject):
    coinIndexChanged = QSignal()
    expandedChanged = QSignal()
    addressIndexChanged = QSignal()
    coinModelChanged = QSignal()
    renderCell = QSignal(int, arguments=["index"])
    emptyBalancesChanged = QSignal()
    addressValid = QSignal(int, str, bool, arguments=[
                                  "coin", "address", "valid"])

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application

        self.__current_coin_idx = -1
        self.__coin_expanded = False
        self.__current_address_idx = -1
        tx_source = tx_model.TxModel(self)
        self.__tx_model = tx_model.TxProxyModel(self)
        self.__tx_model.setSourceModel(tx_source)
        self.__coins_model = coin_model.CoinModel(self)
        self._application.networkThread.heightChanged.connect(self.coin_height_changed)
        self.showEmptyBalances = True
        self.coinModelChanged.connect(
            self.update_coin_model, qt_core.Qt.QueuedConnection)

    def update_coin_model(self):
        if self.thread() == qt_core.QThread.currentThread():
            self.__coins_model.reset()
            #
            self.__coins_model.reset_complete()
        else:
            self.coinModelChanged.emit()

    def coin_height_changed(self, coin: 'coins.CoinType') -> None:
        # log.critical(f"COIN HEIGHT CHANGED for {coin} => current {self.coin}")
        if coin == self.coin:
            self.__tx_model.update_confirm_count()

    @qt_core.Property(qt_core.QObject, constant=True)
    def coinModel(self) -> qt_core.QObject:
        return self.__coins_model

    @qt_core.Property('QVariantList', constant=True)
    def staticCoinModel(self) -> 'QVariantList':
        return self._application.coinList

    @qt_core.Property(int, notify=coinIndexChanged)
    def coinIndex(self) -> int:
        return self.__current_coin_idx

    @qt_core.Property(bool, notify=expandedChanged)
    def expanded(self) -> bool:
        return self.__coin_expanded

    @qt_core.Property(str, notify=coinIndexChanged)
    def unit(self) -> str:
        """
        sugar.. don't delete please
        """
        return self.coin.unit if self.coin is not None else "BTC"  # pylint: disable=no-member

    @qt_core.Property(coins.CoinType, notify=coinIndexChanged)
    def coin(self) -> 'coins.CoinType':
        if self.__current_coin_idx >= 0:
            return self._application.coinList[self.__current_coin_idx]

    @qt_core.Property(address.CAddress, notify=addressIndexChanged)
    def address(self) -> address.CAddress:
        coin = self.coin
        if coin is not None:
            assert self.__current_address_idx < len(
                coin), f"{self.__current_address_idx} < {len(coin)}"
            if self.__current_address_idx >= 0:
                return coin(self.__current_address_idx)  # pylint: disable=unsubscriptable-object
            return coin.root

    @qt_core.Property(int, notify=addressIndexChanged)
    def addressIndex(self) -> int:
        return self.__current_address_idx

    @coinIndex.setter
    def __set_coin_index(self, idx: int):
        if idx == self.__current_coin_idx:
            return
        assert idx < len(self._application.coinList)
        if self.coin is not None and self.__current_address_idx >= 0:
            self.coin.current_wallet = self.__current_address_idx
            # log.debug("Current wallet: %s", self.__current_address_idx)
        self.__current_coin_idx = idx
        self.__set_address_index(-1, force=True)
        self.update_tx_model()
        # self.addressIndexChanged.emit()
        self.coinIndexChanged.emit()

    @expanded.setter
    def __set_expanded(self, value: bool):
        if self.__coin_expanded == value:
            return
        # log.warning(f"value: {value} empty:{self.coin.empty(not self.showEmptyBalances)}")
        if value and self.coin.empty(not self.showEmptyBalances):
            return
        # log.warning(f"coin ex: {value}")
        self.__coin_expanded = value
        self.expandedChanged.emit()
        self.__set_address_index(-1)

    @addressIndex.setter
    def __set_address_index(self, idx: int,  force: bool = False):
        # it happens if no wallets
        # log.warning(f"wallet index: {idx} old:{self.__current_address_idx}")
        if (idx == self.__current_address_idx and not force) or idx >= len(self.coin):
            return
        self.__current_address_idx = idx
        self.update_tx_model()
        self.addressIndexChanged.emit()
        if idx >= 0:
            self._application.networkThread.update_wallet(self.address)

    @qt_core.Property(str, constant=True)
    def currency(self) -> str:
        return "USD"  # TODO

    @qt_core.Slot()
    def deleteCurrentWallet(self):
        if self.address:
            self._application.databaseThread.delete_wallet(self.address)
            self.addressIndex = 0

    @qt_core.Property(qt_core.QObject, constant=True)
    def txModel(self) -> qt_core.QObject:
        return self.__tx_model

    @qt_core.Property(bool, notify=emptyBalancesChanged)
    def showEmptyBalances(self) -> bool:
        return self.__coins_model.show_empty_addresses

    @showEmptyBalances.setter
    def __set_show_empty_balances(self, value=bool):
        if self.__coins_model.show_empty_addresses == value:
            return
        self.__coins_model.show_empty_addresses = value
        for c in self._application.coinList:
            c.show_empty = value
        self.emptyBalancesChanged.emit()
        # yeah!
        self.addressIndexChanged.emit()

    def update_tx_model(self):
        self.__tx_model.address = self.address

    @qt_core.Slot()
    def getCoinUnspentList(self):
        if self.coin:
            # TODO: we shouldn't get unspents from read only addresses
            for addr in self.coin:  # pylint: disable=not-an-iterable
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

    @qt_core.Slot(int, str)
    def validateAddress(self, coin_index: int, name: str) -> None:
        self._application.networkThread.validate_address(coin_index, name)

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

    @qt_core.Slot()
    def makeDummyTx(self):
        addr = self.address
        if addr.is_root:
            addr = addr()
        if addr:
            tx = addr.make_dummy_tx(addr)
            log.debug(f"dummy transaction made: {tx}")
            addr.add_tx(tx, check_new=True)

    def address_validated_handler(self, coin: 'coins.CoinType', address: str, result: bool) -> None:
        for c in self._application.coinList:
            if c is coin:
                self.addressValid.emit(c, address, result)
                return
        pass

    def update_tx(self, tx_: 'tx.Transaction') -> None:
        if self.address == tx_.wallet:
            # TODO: !!! use tx
            self.__tx_model.update_confirm_count(3)

    def render_cell(self, coin):
        for c in self._application.coinList:
            if c is coin:
                self.renderCell.emit(c)
                return

    @qt_core.Slot()
    def addTxRow(self):
        source: address.CAddress = self.address
        assert source
        tx_: tx.Transaction = source.make_dummy_tx()
        tx_.height = self.coin.height + 1
        source.add_tx(tx_)

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
