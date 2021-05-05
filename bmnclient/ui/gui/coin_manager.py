from __future__ import annotations
import logging
from typing import TYPE_CHECKING

import PySide2.QtCore as qt_core
from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal
from ...wallet import coins
from . import import_export
from ...models.coin import CoinListModel

if TYPE_CHECKING:
    from . import Application

log = logging.getLogger(__name__)


class CoinManager(QObject):
    coinIndexChanged = QSignal()
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
        self.coinIndexChanged.emit()

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
        # self._run_cmd(net_cmd.AddressInfoApiQuery(wallet, self))
        pass
