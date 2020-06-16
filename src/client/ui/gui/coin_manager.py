
import logging
import PySide2.QtCore as qt_core
import PySide2.QtQml as qt_qml
from client.wallet import coins
from client.wallet import address
from . import import_export
from client.wallet import key

log = logging.getLogger(__name__)


class CoinManager(qt_core.QObject):
    coinIndexChanged = qt_core.Signal()
    addressIndexChanged = qt_core.Signal()
    addressModelChanged = qt_core.Signal()
    txModelChanged = qt_core.Signal()
    coinModelChanged = qt_core.Signal()
    emptyBalancesChanged = qt_core.Signal()

    def __init__(self, gcd, parent):
        super().__init__(parent=parent)
        self._gcd = gcd
        self._current_coin_idx = -1
        self._current_address_idx = -1
        self._tx_model = []
        # 0 - all 1- sent 2 - recv
        self._tx_sorting_order = 0
        self._show_empty_balances = True

    def update_coin_model(self):
        self.coinModelChanged.emit()

    def on_incoming_transfer(self, tx_: "Transaction"):
        # don't know what to do
        log.debug(f"have bew TX: {tx_}")
        self.parent().uiManager.statusMessage = self.tr(
            "Incoming transfer %s %s from '%s'" % (tx_.balanceHuman, tx_.unit, tx_.fromAddress))

    @qt_core.Property('QVariantList', notify=coinModelChanged)
    def coinModel(self) -> 'QVariantList':
        return self._gcd.all_visible_coins

    @qt_core.Property('QVariantList', constant=True)
    def staticCoinModel(self) -> 'QVariantList':
        return self._gcd.all_coins

    @qt_core.Property(int, notify=coinIndexChanged)
    def coinIndex(self) -> int:
        return self._current_coin_idx

    @qt_core.Property(str, notify=coinIndexChanged)
    def unit(self) -> str:
        """
        sugar.. don't delete please
        """
        return self.coin.unit if self.coin else coins.BitCoin.unit  # pylint: disable=no-member

    @qt_core.Property(coins.CoinType, notify=addressIndexChanged)
    def coin(self) -> coins.CoinType:
        if self._current_coin_idx >= 0:
            return self._gcd.all_visible_coins[self._current_coin_idx]

    @qt_core.Property(address.CAddress, notify=addressIndexChanged)
    def address(self) -> address.CAddress:
        coin = self.coin
        if coin:
            if self._current_address_idx >= 0 and self._current_address_idx < len(coin):
                return coin[self._current_address_idx]  # pylint: disable=unsubscriptable-object

    @qt_core.Property(int, notify=addressIndexChanged)
    def addressIndex(self) -> int:
        return self._current_address_idx

    @coinIndex.setter
    def _set_coin_index(self, idx: int):
        """
        one tough point here - if we change coin we also have to change addres anyway
        """
        if idx == self._current_coin_idx:
            return
        assert idx < len(self._gcd.all_coins)
        log.debug("New current coin: %s", self._current_coin_idx)
        if self.coin and self._current_address_idx >= 0:
            self.coin.current_wallet = self._current_address_idx
            log.debug("Current wallet: %s", self._current_address_idx)
        self._current_coin_idx = idx
        if idx >= 0:
            self._set_address_index(self.coin.current_wallet, force=True)
            self.txModelChanged.emit()
        self.coinIndexChanged.emit()

    @addressIndex.setter
    def _set_address_index(self, idx: int,  force: bool = False):
        # it happens if no wallets
        if (idx == self._current_address_idx and not force) or idx >= len(self.coin):
            return
        self._current_address_idx = idx
        self.address.txListChanged.connect(
            self.updateTxList, qt_core.Qt.QueuedConnection)
        self.addressIndexChanged.emit()
        self.updateTxList()

    @qt_core.Property(str, constant=True)
    def currency(self) -> str:
        return ""

    @qt_core.Slot()
    def deleteCurrentWallet(self):
        if self.address:
            self._gcd.delete_wallet(self.address)
            self.addressIndex = 0
            self.addressModelChanged.emit()

    @qt_core.Slot()
    def clear(self):
        """
        removes all addresses
        """
        self._gcd.delete_all_wallets()
        self.coinIndex = -1
        self.addressModelChanged.emit()

    @qt_core.Property('QVariantList', notify=txModelChanged)
    def txModel(self) -> 'QVariantList':
        return self._tx_model

    @qt_core.Property(bool, notify=emptyBalancesChanged)
    def showEmptyBalances(self) -> bool:
        return self._show_empty_balances

    @showEmptyBalances.setter
    def _set_show_empty_balances(self, value=bool):
        if self._show_empty_balances == value:
            return
        self._show_empty_balances = value
        for c  in self._gcd.all_coins:
            c.show_empty = value
            c.walletListChanged.emit()
        self.emptyBalancesChanged.emit()

    @qt_core.Property(int, notify=txModelChanged)
    def txSortingOrder(self) -> int:
        return self._tx_sorting_order

    def updateTxList(self):
        if self.address:
            if self._tx_sorting_order == 1:
                self._tx_model = [
                    tx for tx in self.address.txs if tx.sent]  # pylint: disable=no-member
            elif self._tx_sorting_order == 2:
                self._tx_model = [
                    tx for tx in self.address.txs if not tx.sent]  # pylint: disable=no-member
            else:
                self._tx_model = self.address.txs  # pylint: disable=no-member
            log.debug(f"tx list {len(self._tx_model)}")
            self.txModelChanged.emit()

    @txSortingOrder.setter
    def _set_tx_sorting_order(self, order: int):
        if self._tx_sorting_order == order:
            return
        self._tx_sorting_order = order
        log.debug(f"new TX sorting order: {order}")
        self.updateTxList()

    @qt_core.Slot(int, result=int)
    def walletsCount(self, coin_index: int) -> int:
        return len(self._gcd.all_coins[coin_index])

    @qt_core.Slot()
    def getCoinUnspentList(self):
        if self.coin:
            # TODO: we shouldn't get unspents from read only addresses
            for addr in self.coin:  # pylint: disable=not-an-iterable
                if not addr.readOnly and addr.balance > 0:
                    self._gcd.unspent_list(addr)
        else:
            log.warn("No current coin")

    @qt_core.Slot()
    def getAddressUnspentList(self):
        if self.address:
            self._gcd.unspent_list(self.address)

    @qt_core.Slot(int, str, bool)
    def makeAddress(self, coin_index: int, label: str, segwit: bool):
        if coin_index >= 0:
            log.debug(f"Coin idx:{coin_index}")
            try:
                coin = self._gcd.all_visible_coins[coin_index]
                coin.make_address(
                    key.AddressType.P2WPKH if segwit else key.AddressType.P2PKH, label)
                self.addressModelChanged.emit()
            except address.AddressError as ca:
                log.error(f"Can't make new address: {ca}")
        else:
            log.error(f"No coin selected {coin_index}!")

    @qt_core.Slot(int, str, str)
    def addWatchAddress(self, coin_index: int, name: str, label: str):
        if coin_index >= 0:
            log.debug(f"Coin idx:{coin_index}")
            try:
                coin: coins.CoinType = self._gcd.all_visible_coins[coin_index]
                coin.add_watch_address(name, label)
                self.addressModelChanged.emit()
            except address.AddressError as ca:
                log.error(f"Can't add watch address: {ca}")
        else:
            log.error(f"No coin selected {coin_index}!")

    @qt_core.Slot(int)
    def clearTransactions(self, address_index: int):
        log.debug(f"clearing tx list of adress: {self.address}")
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self._current_coin_idx} address:{address_index}")
            return
        self._gcd.clear_transactions(self.coin[address_index])
        self.txModelChanged.emit()

    @qt_core.Slot(int)
    def removeAddress(self, address_index: int):
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self._current_coin_idx} address:{address_index}")
            return
        log.debug(f"removing adress: {address_index}")
        self._gcd.delete_wallet(self.coin[address_index])
        self.txModelChanged.emit()

    @qt_core.Slot(str, str)
    def exportWallet(self, fpath: str, password: str):
        return self._gcd.export_wallet(fpath, password)

    @qt_core.Slot(str, str)
    def importWallet(self, fpath: str, password: str):
        return self._gcd.import_wallet(fpath, password)

    @qt_core.Slot(int)
    def exportTransactions(self, address_index: int):
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self._current_coin_idx} address:{address_index}")
            return
        iexport = import_export.ImportExportDialog()
        filename = iexport.doExport(
            self.tr("Select file to save transactions"), ".json")
        self.coin[address_index].export_txs(filename)

    @qt_core.Slot(int)
    def updateAddress(self, address_index: int):
        if self.coin is None or address_index < 0:
            log.critical(
                f"invalid coin idecies: coin:{self._current_coin_idx} address:{address_index}")
            return
        self._gcd.updateAddress.emit(self.coin[address_index])

    @qt_core.Slot()
    def makeDummyTx(self):
        addr: address.CAddress = self.address
        if addr:
            tx = addr.make_dummy_tx()
            log.debug(f"dummy transaction made: {tx}")
        else:
            log.critical("Can't make dummy TX: no current address")

    @qt_core.Slot()
    def debugHistoryRequest(self):
        addr: address.CAddress = self.address
        if addr:
            self._gcd.debugUpdateHistory.emit(addr)
        else:
            log.warning("No current address")

    @qt_core.Slot()
    def retrieveAddressMempool(self):
        addr: address.CAddress = self.address
        if addr:
            self._gcd.mempoolAddress.emit(addr)
        else:
            log.warning("No current address")

    @qt_core.Slot()
    def retrieveCoinMempool(self):
        coin: coins.CoinType = self.coin
        if coin:
            self._gcd.mempoolCoin.emit(coin)
        else:
            log.warning("No current coin")
