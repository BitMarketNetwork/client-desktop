from __future__ import annotations

import logging
import math
from typing import List, Optional, TYPE_CHECKING, Tuple

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from ...config import UserConfig
from ...language import Language
from ...wallet import currency

if TYPE_CHECKING:
    from . import Application

log = logging.getLogger(__name__)


class SettingsManager(QObject):
    DEFAULT_FONT_SIZE = 10
    newAddressChanged = QSignal()
    currencyChanged = QSignal()

    def __init__(self, application: Application) -> None:
        super().__init__()

        self._use_new_address = True
        #
        self._currency_model = []
        self._currency_index = 0
        self._fill_currencies()
        #


        self._application = application

        self._language_list: Optional[List[str]] = None
        self._current_language_name: Optional[str] = None
        self._current_theme_name: Optional[str] = None
        self._hide_to_tray: Optional[bool] = None
        self._font: Optional[Tuple] = None
        self._default_font = self._application.defaultFont

    def _fill_currencies(self):
        currencies = [
            (self.tr("US dollar"), "USD"),
            (self.tr("Euro"), "EUR"),
            (self.tr("Russian ruble"), "RUB"),
        ]
        self._currency_model = [
            currency.Currency(
                self,
                name=name,
            )
            for name, _ in currencies
        ]

    ############################################################################
    # FiatRateService
    ############################################################################

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
            self.fiatRateServiceChanged.emit()

    ############################################################################
    # Language
    ############################################################################

    currentLanguageNameChanged = QSignal()

    @QProperty('QVariantList', constant=True)
    def languageList(self) -> list:
        if self._language_list is None:
            self._language_list = Language.createTranslationList()
        assert type(self._language_list) is list
        return self._language_list

    def _isValidLanguageName(self, name) -> bool:
        if type(name) is str:
            language_list = self.languageList
            for i in range(0, len(language_list)):
                if name == language_list[i]['name']:
                    return True
        return False

    @QProperty(str, notify=currentLanguageNameChanged)
    def currentLanguageName(self) -> str:
        if self._current_language_name is None:
            name = self._application.userConfig.get(
                UserConfig.KEY_UI_LANGUAGE,
                str,
                Language.PRIMARY_NAME)
            if self._isValidLanguageName(name):
                self._current_language_name = name
            else:
                self._current_language_name = Language.PRIMARY_NAME
        assert type(self._current_language_name) is str
        return self._current_language_name

    @currentLanguageName.setter
    def _setCurrentLanguageName(self, name: str) -> None:
        assert type(name) is str
        if not self._isValidLanguageName(name):
            log.error(f"Unknown language \"{name}\".")
            return
        self._application.userConfig.set(UserConfig.KEY_UI_LANGUAGE, name)
        if self._current_language_name != name:
            self._current_language_name = name
            self.currentLanguageNameChanged.emit()

    @QSlot(result=int)
    def currentLanguageIndex(self) -> int:
        name = self.currentLanguageName
        language_list = self.languageList
        for i in range(0, len(language_list)):
            if name == language_list[i]['name']:
                return i
        assert False
        return -1

    ############################################################################
    # Theme
    ############################################################################

    currentThemeNameChanged = QSignal()

    @QProperty(str, notify=currentThemeNameChanged)
    def currentThemeName(self) -> str:
        if self._current_theme_name is None:
            self._current_theme_name = self._application.userConfig.get(
                UserConfig.KEY_UI_THEME,
                str,
                ""  # QML controlled
            )
        assert type(self._current_theme_name) is str
        return self._current_theme_name

    @currentThemeName.setter
    def _setCurrentThemeName(self, name: str) -> None:
        assert type(name) is str
        self._application.userConfig.set(UserConfig.KEY_UI_THEME, name)
        if self._current_theme_name != name:
            self._current_theme_name = name
            self.currentThemeNameChanged.emit()

    ############################################################################
    # HideToTray
    ############################################################################

    hideToTrayChanged = QSignal()

    @QProperty(bool, notify=hideToTrayChanged)
    def hideToTray(self) -> bool:
        if self._hide_to_tray is None:
            self._hide_to_tray = self._application.userConfig.get(
                UserConfig.KEY_UI_HIDE_TO_TRAY,
                bool,
                False)
        assert type(self._hide_to_tray) is bool
        return self._hide_to_tray

    @hideToTray.setter
    def _setHideToTray(self, value) -> None:
        assert type(value) is bool
        self._application.userConfig.set(UserConfig.KEY_UI_HIDE_TO_TRAY, value)
        if value != self._hide_to_tray:
            self._hide_to_tray = value
            self.hideToTrayChanged.emit()

    ############################################################################
    # Font
    ############################################################################

    fontChanged = QSignal()

    @QProperty("QVariantMap", notify=fontChanged)
    def font(self) -> dict:
        if self._font is None:
            with self._application.userConfig.lock:
                family = self._application.userConfig.get(
                    UserConfig.KEY_UI_FONT_FAMILY,
                    str,
                    None)
                size = self._application.userConfig.get(
                    UserConfig.KEY_UI_FONT_SIZE,
                    int,
                    0)
            if not family:
                family = self._default_font.family()
            if not size:
                size = self._default_font.pointSize()
            if size <= 0:
                size = self.DEFAULT_FONT_SIZE
            self._font = (family, size)

        # QML Qt.font() comfortable
        return {
            "family": self._font[0],
            "pointSize": self._font[1]
        }

    @font.setter
    def _setFont(self, font: dict) -> None:
        # QML Qt.font() comfortable
        if "family" in font:
            family = str(font["family"])
        else:
            family = self._default_font.family()
        if "pointSize" in font:
            size = int(font["pointSize"])
            size = self.DEFAULT_FONT_SIZE if size <= 0 else size
        else:
            size = self.DEFAULT_FONT_SIZE

        with self._application.userConfig.lock:
            self._application.userConfig.set(
                UserConfig.KEY_UI_FONT_FAMILY,
                family,
                save=False)
            self._application.userConfig.set(
                UserConfig.KEY_UI_FONT_SIZE,
                size,
                save=False)
            self._application.userConfig.save()

        if (family, size) != self._font:
            self._font = (family, size)
            self.fontChanged.emit()

    ############################################################################
    # TODO
    ############################################################################

    @QProperty("QVariantList", constant=True)
    def currencyModel(self):
        return self._currency_model

    @QProperty(int, notify=currencyChanged)
    def currencyIndex(self) -> int:
        return self._currency_index

    @currencyIndex.setter
    def _set_currency(self, index: int):
        if index == self._currency_index:
            return
        self._currency_index = index
        self.currencyChanged.emit()

    @QProperty(currency.Currency, notify=currencyChanged)
    def currency(self) -> currency.Currency:
        if self._currency_index < len(self._currency_model):
            return self._currency_model[self._currency_index]

    @QSlot(float, result=str)
    def coinBalance(self, amount: float) -> str:
        assert isinstance(amount, (int, float)), amount
        if math.isnan(amount):
            return "0"
        # log.debug(f"balance calcaultaion")
        try:
            res = amount / pow(10, 8)
            if res == 0.0:
                return "0"
            res = format(round(res, max(0, 3 - int(math.log10(res)))), 'f')
            if '.' in res:
                return res.rstrip("0.") or "0"
        except ValueError as ve:
            raise ValueError(f"{ve} for {amount} and {res}") from ve
        except OverflowError as oe:
            log.error(f"Overflow {amount}")
            raise OverflowError(f"{oe} for {res}") from oe

    @QProperty(bool, notify=newAddressChanged)
    def newAddressFroLeftover(self) -> bool:
        return self._use_new_address

    @newAddressFroLeftover.setter
    def _set_use_new_address(self, on: bool) -> None:
        if on == self._use_new_address:
            return
        self._use_new_address = on
        self.newAddressChanged.emit()
