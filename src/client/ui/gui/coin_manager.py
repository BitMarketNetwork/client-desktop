
import logging

import PySide2.QtCore as qt_core
import PySide2.QtQml as qt_qml

from ... import constant
from ...wallet import address, coin_model, coins, key, tx, tx_model
from . import import_export

log = logging.getLogger(__name__)


class CoinManager(qt_core.QObject):
    coinIndexChanged = qt_core.Signal()
    addressIndexChanged = qt_core.Signal()
    coinModelChanged = qt_core.Signal()
    emptyBalancesChanged = qt_core.Signal()
    addressValid = qt_core.Signal(int, str, bool, arguments=[
                                  "coin", "address", "valid"])

    def __init__(self, gcd: 'gcd.GCD', parent):
        super().__init__(parent=parent)
        self.__gcd: 'gcd.GCD' = gcd
        self.__current_coin_idx = -1
        self.__current_address_idx = -1
        tx_source = tx_model.TxModel(self)
        self.__tx_model = tx_model.TxProxyModel(self)
        self.__tx_model.setSourceModel(tx_source)
        self.__coins_model = coin_model.CoinModel(self, gcd)
        gcd.heightChanged.connect(self.coin_height_changed)
        self.showEmptyBalances = gcd.get_settings(
            constant.SHOW_EMPTY_BALANCES, False, bool)
        self.coinModelChanged.connect(
            self.update_coin_model, qt_core.Qt.QueuedConnection)

    def update_coin_model(self):
        if self.thread() == qt_core.QThread.currentThread():
            self.__coins_model.reset()
            #
            self.__coins_model.reset_complete()
        else:
            self.coinModelChanged.emit()

    def coin_height_changed(self, coin: coins.CoinType) -> None:
        # log.critical(f"COIN HEIGHT CHANGED for {coin} => current {self.coin}")
        if coin == self.coin:
            self.__tx_model.update_confirm_count()

    def on_incoming_transfer(self, tx_: "Transaction"):
        # don't know what to do
        log.debug(f"have bew TX: {tx_}")
        self.parent().uiManager.statusMessage = self.tr(
            "Incoming transaction %s %s" % (tx_.balanceHuman, tx_.unit))

    @qt_core.Property(qt_core.QObject, constant=True)
    def coinModel(self) -> qt_core.QObject:
        return self.__coins_model

    @qt_core.Property('QVariantList', constant=True)
    def staticCoinModel(self) -> 'QVariantList':
        return self.__gcd.all_coins

    @qt_core.Property(int, notify=coinIndexChanged)
    def coinIndex(self) -> int:
        return self.__current_coin_idx

    @qt_core.Property(str, notify=coinIndexChanged)
    def unit(self) -> str:
        """
        sugar.. don't delete please
        """
        return self.coin.unit if self.coin else coins.BitCoin.unit  # pylint: disable=no-member

    @qt_core.Property(coins.CoinType, notify=coinIndexChanged)
    def coin(self) -> coins.CoinType:
        if self.__current_coin_idx >= 0:
            return self.__gcd[self.__current_coin_idx]

    @qt_core.Property(address.CAddress, notify=addressIndexChanged)
    def address(self) -> address.CAddress:
        coin = self.coin
        if coin:
            if self.__current_address_idx >= 0 and self.__current_address_idx < len(coin):
                return coin(self.__current_address_idx)  # pylint: disable=unsubscriptable-object

    @qt_core.Property(int, notify=addressIndexChanged)
    def addressIndex(self) -> int:
        return self.__current_address_idx

    @coinIndex.setter
    def _set_coin_index(self, idx: int):
        """
        one tough point here - if we change coin we also have to change addres anyway
        """
        if idx == self.__current_coin_idx:
            return
        assert idx < len(self.__gcd)
        if self.coin and self.__current_address_idx >= 0:
            self.coin.current_wallet = self.__current_address_idx
            log.debug("Current wallet: %s", self.__current_address_idx)
        self.__current_coin_idx = idx
        log.debug("New current coin: %s", self.__current_coin_idx)
        if idx >= 0:
            self._set_address_index(self.coin.current_wallet, force=True)
        self.coinIndexChanged.emit()

    @addressIndex.setter
    def _set_address_index(self, idx: int,  force: bool = False):
        # it happens if no wallets
        if (idx == self.__current_address_idx and not force) or idx >= len(self.coin):
            return
        self.__current_address_idx = idx
        self.updateTxList()
        self.addressIndexChanged.emit()
        addr = self.address
        if addr:
            self.__gcd.update_wallet(addr)

    @qt_core.Property(str, constant=True)
    def currency(self) -> str:
        return ""

    @qt_core.Slot()
    def deleteCurrentWallet(self):
        if self.address:
            self.__gcd.delete_wallet(self.address)
            self.addressIndex = 0

    @qt_core.Property(qt_core.QObject, constant=True)
    def txModel(self) -> qt_core.QObject:
        return self.__tx_model

    @qt_core.Property(bool, notify=emptyBalancesChanged)
    def showEmptyBalances(self) -> bool:
        return self.__coins_model.show_empty_addresses

    @showEmptyBalances.setter
    def _set_show_empty_balances(self, value=bool):
        if self.__coins_model.show_empty_addresses == value:
            return
        self.__coins_model.show_empty_addresses = value
        self.__gcd.set_settings(constant.SHOW_EMPTY_BALANCES, value)
        for c in self.__gcd.all_coins:
            c.show_empty = value
        self.emptyBalancesChanged.emit()
        # yeah!
        self.addressIndexChanged.emit()

    def updateTxList(self):
        self.__tx_model.address = self.address

    @qt_core.Slot(int, result=int)
    def walletsCount(self, coin_index: int) -> int:
        return len(self.__gcd.all_coins[coin_index])

    @qt_core.Slot()
    def getCoinUnspentList(self):
        if self.coin:
            # TODO: we shouldn't get unspents from read only addresses
            for addr in self.coin:  # pylint: disable=not-an-iterable
                if not addr.readOnly and addr.balance > 0:
                    self.__gcd.unspent_list(addr)
        else:
            log.warn("No current coin")

    @qt_core.Slot()
    def getAddressUnspentList(self):
        if self.address:
            self.__gcd.unspent_list(self.address)

    @qt_core.Slot(int, str, bool)
    def makeAddress(self, coin_index: int, label: str, segwit: bool):
        if coin_index >= 0:
            log.debug(f"Coin idx:{coin_index}")
            try:
                coin = self.__gcd[coin_index]
                coin.make_address(
                    key.AddressType.P2WPKH if segwit else key.AddressType.P2PKH, label)
            except address.AddressError as ca:
                log.error(f"Can't make new address: {ca}")
        else:
            log.error(f"No coin selected {coin_index}!")

    @qt_core.Slot(int, str)
    def validateAddress(self, coin_index: int, name: str) -> None:
        self.__gcd.validate_address(coin_index, name)

    @qt_core.Slot(int, str, str)
    def addWatchAddress(self, coin_index: int, name: str, label: str) -> None:
        """
        no checks here !!!
        """
        if coin_index >= 0:
            log.debug(f"Coin idx:{coin_index}")
            coin: coins.CoinType = self.__gcd[coin_index]
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
        self.__gcd.clear_transactions(addrss)
        self.__tx_model.clear_complete(addrss)

    @qt_core.Slot(int)
    def removeAddress(self, address_index: int):
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self.__current_coin_idx} address:{address_index}")
            return
        log.debug(f"removing adress: {address_index}")
        self.__gcd.delete_wallet(
            self.coin[address_index])  # pylint: disable=unsubscriptable-object
        self.__tx_model.clear(self.coin[address_index])

    @qt_core.Slot(str, str)
    def exportWallet(self, fpath: str, password: str):
        return self.__gcd.export_wallet(fpath, password)

    @qt_core.Slot(str, str)
    def importWallet(self, fpath: str, password: str):
        return self.__gcd.import_wallet(fpath, password)

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
        self.__gcd.updateAddress.emit(
            self.coin[address_index])  # pylint: disable=unsubscriptable-object

    @qt_core.Slot()
    def makeDummyTx(self):
        addr: address.CAddress = self.address
        if addr:
            tx = addr.make_dummy_tx()
            log.debug(f"dummy transaction made: {tx}")

    @qt_core.Slot()
    def debugHistoryRequest(self):
        addr: address.CAddress = self.address
        if addr:
            self.__gcd.debugUpdateHistory.emit(addr)
        else:
            log.warning("No current address")

    @qt_core.Slot()
    def retrieveAddressMempool(self):
        addr: address.CAddress = self.address
        if addr:
            self.__gcd.mempoolAddress.emit(addr)
        else:
            log.warning("No current address")

    @qt_core.Slot()
    def retrieveCoinMempool(self):
        coin: coins.CoinType = self.coin
        if coin:
            self.__gcd.mempoolCoin.emit(coin)
        else:
            log.warning("No current coin")

    def address_validated_handler(self, coin: coins.CoinType, address: str, result: bool) -> None:
        self.addressValid.emit(
            self.__gcd.all_visible_coins.index(coin), address, result)

    def update_tx(self, tx_: 'tx.Transaction') -> None:
        if self.address == tx_.wallet:
            # TODO: !!! use tx
            self.__tx_model.update_confirm_count(3)

    @qt_core.Slot()
    def lookForHD(self):
        self.__gcd.look_for_HD()

    @qt_core.Slot()
    def clear(self):
        """
        removes all addresses
        """
        self.__gcd.delete_all_wallets()
        self.coinIndex = -1
        self.lookForHD()

    @qt_core.Slot(int)
    def updateCoin(self, index: int):
        self.__gcd.update_coin(index)

    @qt_core.Slot(int)
    def clearCoin(self, index: int):
        self.__gcd.clear_coin(index)

    @qt_core.Slot()
    def fakeTxStatusProgress(self):
        coin: coins.CoinType = self.coin
        if not coin or len(coin) < 2:
            raise RuntimeError(
                f"Active coin and at least two addresses in it required for simulation")

        from ...wallet import mutable_tx, tx
        from ... import gcd
        source: address.CAddress = coin(0)
        reciever = coin(1)
        assert source != reciever

        def make_tx(w: address.CAddress):
            tx_: tx.Transaction = w.make_dummy_tx()
            tx_.height = coin.height + 1
            tx_.add_inputs(((1000000, source.name),), True)
            tx_.add_inputs(((1000000, reciever.name),), False)
            return tx_
        log.warning(f"source: {source} target: {reciever}")
        #
        tx_ = make_tx(source)
        source.add_tx(tx_)
        reciever.add_tx(tx_)
        self.__gcd.fakeMempoolSearch.emit(tx_)

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
