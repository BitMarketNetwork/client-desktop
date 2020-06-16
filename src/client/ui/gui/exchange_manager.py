
import logging

import PySide2.QtCore as qt_core
from typing import Any, Optional
from . import coin_manager
from client.wallet import abs_coin
from client import gcd
log = logging.getLogger(__name__)


class ExchangeManager(qt_core.QObject):
    sourceCoinChanged = qt_core.Signal()
    targetCoinChanged = qt_core.Signal()
    sourceAmountChanged = qt_core.Signal()
    targetAmountChanged = qt_core.Signal()
    sourceFiatAmountChanged = qt_core.Signal()
    targetFiatAmountChanged = qt_core.Signal()

    def __init__(self, parent: Optional[qt_core.QObject]):
        super().__init__(parent)
        self._gcd = gcd.GCD.get_instance()
        self._source_model = [
            coin for coin in self._gcd.all_coins if not coin.test and coin.enabled]
        self._target_model = [
            coin for coin in self._gcd.all_coins if not coin.test and coin.enabled]

        self._source_amount = 100
        self._target_amount = 100
        # log.warning(f"source  ex model:{self._source_model}")
        # log.warning(f"target  ex model:{self._target_model}")
        self._source_index = 0
        # use setter for logic
        self._target_index = 1

    def _change_amount(self, amount: float, plus: bool) -> float:
        if plus:
            return (amount * 1.1)
        return max(0, amount * 0.9)

    def _to_human(self, amount: float) -> str:
        return "{:.2f}".format(amount)

    @property
    def coin_man(self):
        return self.parent().coinManager

    @qt_core.Property("QVariantList", constant=True)
    def sourceModel(self) -> "QVariantList":
        return self._source_model

    @qt_core.Property("QVariantList", constant=True)
    def targetModel(self) -> "QVariantList":
        return self._target_model

    @qt_core.Property(int, notify=sourceCoinChanged)
    def sourceIndex(self) -> int:
        return self._source_index

    @sourceIndex.setter
    def _set_source_coin(self, idx: int):
        if idx == self._source_index:
            return
        self._source_index = idx
        self.sourceCoinChanged.emit()
        self.sourceFiatAmountChanged.emit()

    @qt_core.Property(int, notify=targetCoinChanged)
    def targetIndex(self) -> int:
        return self._target_index

    @targetIndex.setter
    def _set_target_coin(self, idx: int):
        log.debug(f"target idx: {idx} {self._target_index}")
        if idx == self._target_index:
            return
        self._target_index = idx
        self.targetCoinChanged.emit()
        self.targetFiatAmountChanged.emit()
        # check the same
        if self.targetCoin == self.sourceCoin:
            idx = next((i for i in range(0, len(self._source_model))
                        if i != self._target_index), None)
            if idx is not None:
                # no recursion here
                self.sourceIndex = idx

    @qt_core.Property(abs_coin.CoinBase, notify=sourceCoinChanged)
    def sourceCoin(self) -> abs_coin.CoinBase:
        if self._source_index < len(self._source_model):
            return self._source_model[self._source_index]

    @qt_core.Property(abs_coin.CoinBase, notify=targetCoinChanged)
    def targetCoin(self) -> abs_coin.CoinBase:
        if self._target_index < len(self._target_model):
            return self._target_model[self._target_index]

    @qt_core.Property(str, notify=sourceAmountChanged)
    def sourceAmount(self) -> str:
        return self.sourceCoin.balance_human(self._source_amount)# pylint: disable=no-member

    @qt_core.Property(str, notify=targetAmountChanged)
    def targetAmount(self) -> str:
        return self.targetCoin.balance_human(self._target_amount)# pylint: disable=no-member

    @qt_core.Property(str, notify=sourceFiatAmountChanged)
    def sourceFiatAmount(self) -> str:
        return self.sourceCoin.fiat_amount(self._source_amount, False)# pylint: disable=no-member

    @qt_core.Property(str, notify=targetFiatAmountChanged)
    def targetFiatAmount(self) -> str:
        return self.targetCoin.fiat_amount(self._target_amount, False) # pylint: disable=no-member

    @qt_core.Slot()
    def increaseSource(self):
        self._source_amount = self._change_amount(self._source_amount, True)
        self.sourceAmountChanged.emit()
        self.sourceFiatAmountChanged.emit()

    @qt_core.Slot()
    def increaseTarget(self):
        self._target_amount = self._change_amount(self._target_amount, True)
        self.targetAmountChanged.emit()
        self.targetFiatAmountChanged.emit()

    @qt_core.Slot()
    def reduceSource(self):
        self._source_amount = self._change_amount(self._source_amount, False)
        self.sourceAmountChanged.emit()
        self.sourceFiatAmountChanged.emit()

    @qt_core.Slot()
    def reduceTarget(self):
        self._target_amount = self._change_amount(self._target_amount, False)
        self.targetAmountChanged.emit()
        self.targetFiatAmountChanged.emit()

    @qt_core.Property(int, notify=sourceCoinChanged)
    def sourceDecimals(self) -> int:
        if self.sourceCoin:
            return self.sourceCoin.decimalLevel# pylint: disable=no-member
        return 0

    @qt_core.Property(int, notify=targetCoinChanged)
    def targetDecimals(self) -> int:
        if self.targetCoin:
            return self.targetCoin.decimalLevel# pylint: disable=no-member
        return 0
