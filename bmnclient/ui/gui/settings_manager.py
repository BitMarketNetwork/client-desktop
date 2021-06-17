from __future__ import annotations

import logging
from typing import List, Optional, Tuple, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from ...language import Language

if TYPE_CHECKING:
    from . import GuiApplication

log = logging.getLogger(__name__)


class SettingsManager(QObject):
    newAddressChanged = QSignal()
    fiatCurrencyChanged = QSignal()

    fiatRateServiceChanged = QSignal()

    @QProperty(list, constant=True)
    def fiatRateServiceList(self) -> list:
        return [s.fullName for s in self._application.fiatRateServiceList]

    @QProperty(int, notify=fiatRateServiceChanged)
    def currentFiatRateServiceIndex(self) -> int:
        return self._application.fiatRateServiceList.currentIndex

    @currentFiatRateServiceIndex.setter
    def _setCurrentFiatRateServiceIndex(self, index: int) -> None:
        if index != self._application.fiatRateServiceList.currentIndex:
            self._application.fiatRateServiceList.setCurrentIndex(index)
            # noinspection PyUnresolvedReferences
            self.fiatRateServiceChanged.emit()
            self._application.networkQueryScheduler.updateCurrentFiatCurrency()

    ############################################################################
    # FiatCurrency
    ############################################################################

    @QProperty(list, constant=True)
    def fiatCurrencyList(self) -> list:
        return [
            "{} ({})".format(s.name, s.unit)
            for s in self._application.fiatCurrencyList
        ]

    @QProperty(int, notify=fiatCurrencyChanged)
    def currentFiatCurrencyIndex(self) -> int:
        return self._application.fiatCurrencyList.currentIndex

    @currentFiatCurrencyIndex.setter
    def _setCurrentFiatCurrencyIndex(self, index: int):
        if index != self._application.fiatCurrencyList.currentIndex:
            self._application.fiatCurrencyList.setCurrentIndex(index)
            # noinspection PyUnresolvedReferences
            self.fiatCurrencyChanged.emit()
            self._application.networkQueryScheduler.updateCurrentFiatCurrency()
