import logging
import math
import pickle
from typing import Optional, Union

import PySide2.QtCore as QtCore
import bmnclient.config
from . import settings_manager_impl
from ...wallet import base_unit, currency, language, rate_source

log = logging.getLogger(__name__)


class SettingsManager(settings_manager_impl.SettingsManagerImpl):
    newAddressChanged = QtCore.Signal()
    rateSourceChanged = QtCore.Signal()
    currencyChanged = QtCore.Signal()
    unitChanged = QtCore.Signal()

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._language_list = None
        self._current_language_name = None
        self._current_theme_name = None
        self._hide_to_tray = None

    @QtCore.Slot(result=bool)
    def accept(self):
        log.debug("Accepting settings")
        self.parent().coinManager.update_coin_model()
        self._gcd.save_coins_settings()
        return True

    ############################################################################
    # Language
    ############################################################################

    currentLanguageNameChanged = QtCore.Signal()

    @QtCore.Property('QVariantList', constant=True)
    def languageList(self) -> list:
        if self._language_list is None:
            self._language_list = language.Language.createTranslationList()
        assert type(self._language_list) is list
        return self._language_list

    def _isValidLanguageName(self, name) -> bool:
        if type(name) is str:
            language_list = self.languageList
            for i in range(0, len(language_list)):
                if name == language_list[i]['name']:
                    return True
        return False

    @QtCore.Property(str, notify=currentLanguageNameChanged)
    def currentLanguageName(self) -> str:
        if self._current_language_name is None:
            name = self._gcd.get_settings(
                bmnclient.config.UserConfig.KEY_UI_LANGUAGE,
                language.Language.PRIMARY_NAME,
                str)
            if self._isValidLanguageName(name):
                self._current_language_name = name
            else:
                self._current_language_name = language.Language.PRIMARY_NAME
        assert type(self._current_language_name) is str
        return self._current_language_name

    @currentLanguageName.setter
    def _setCurrentLanguageName(self, name) -> None:
        assert type(name) is str
        if not self._isValidLanguageName(name):
            log.error(f"Unknown language \"{name}\".")
            return
        self._gcd.set_settings(bmnclient.config.UserConfig.KEY_UI_LANGUAGE, name)
        if self._current_language_name != name:
            self._current_language_name = name
            self.currentLanguageNameChanged.emit()

    @QtCore.Slot(result=int)
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

    currentThemeNameChanged = QtCore.Signal()

    @QtCore.Property(str, notify=currentThemeNameChanged)
    def currentThemeName(self) -> str:
        if self._current_theme_name is None:
            self._current_theme_name = self._gcd.get_settings(
                bmnclient.config.UserConfig.KEY_UI_THEME,
                "",  # QML controlled
                str)
        assert type(self._current_theme_name) is str
        return self._current_theme_name

    @currentThemeName.setter
    def _setCurrentThemeName(self, name) -> None:
        assert type(name) is str
        self._gcd.set_settings(bmnclient.config.UserConfig.KEY_UI_THEME, name)
        if self._current_theme_name != name:
            self._current_theme_name = name
            self.currentThemeNameChanged.emit()

    ############################################################################
    # HideToTray
    ############################################################################

    hideToTrayChanged = QtCore.Signal()

    @QtCore.Property(bool, notify=hideToTrayChanged)
    def hideToTray(self) -> bool:
        if self._hide_to_tray is None:
            self._hide_to_tray = self._gcd.get_settings(
                bmnclient.config.UserConfig.KEY_UI_HIDE_TO_TRAY,
                False,
                bool)
        assert type(self._hide_to_tray) is bool
        return self._hide_to_tray

    @hideToTray.setter
    def _setHideToTray(self, value) -> None:
        assert type(value) is bool
        self._gcd.set_settings(bmnclient.config.UserConfig.KEY_UI_HIDE_TO_TRAY, value)
        if value != self._hide_to_tray:
            self._hide_to_tray = value
            self.hideToTrayChanged.emit()

    ############################################################################
    # TODO
    ############################################################################

    @QtCore.Property("QVariantList", constant=True)
    def currencyModel(self):
        return self._currency_model

    @QtCore.Property(int, notify=currencyChanged)
    def currencyIndex(self) -> int:
        return self._currency_index

    @currencyIndex.setter
    def _set_currency(self, index: int):
        if index == self._currency_index:
            return
        self._currency_index = index
        self.currencyChanged.emit()

    @QtCore.Property(currency.Currency, notify=currencyChanged)
    def currency(self) -> currency.Currency:
        if self._currency_index < len(self._currency_model):
            return self._currency_model[self._currency_index]

    @QtCore.Property("QVariantList", constant=True)
    def unitModel(self):
        return self._unit_model

    @QtCore.Property(int, notify=unitChanged)
    def unitIndex(self) -> int:
        return self._unit_index

    @unitIndex.setter
    def _set_unit(self, index: Union[int, str]) -> None:
        if isinstance(index, str):
            index = int(index)
        if index == self._unit_index:
            return
        self._unit_index = index
        self._gcd.save_meta("base_unit", str(index))
        self.unitChanged.emit()

    @QtCore.Property(base_unit.BaseUnit, notify=unitChanged)
    def baseUnit(self) -> base_unit.BaseUnit:
        if self._unit_index < len(self._unit_model):
            return self._unit_model[self._unit_index]

    @QtCore.Slot(float, result=str)
    def coinBalance(self, amount: float) -> str:
        # TODO: we disgard coin convertion ratio & decimal level !!! it's
        #  normal for btc & lts but isn't sure for next coins
        assert self.baseUnit
        assert isinstance(amount, (int, float)), amount
        if math.isnan(amount):
            return "0"
        # log.debug(f"balance calcaultaion")
        try:
            # log.warning(f"am:{amount} fac:{self.baseUnit.factor}")
            res = amount / \
                  pow(10, self.baseUnit.factor)  # pylint: disable=no-member
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

    @QtCore.Slot(str, result=str)
    def coinUnit(self, unit: Optional[str]) -> str:
        assert self.baseUnit
        # use current then
        if unit is None:
            unit = self.parent().coinManager.coin.unit
        # unless baseUnit implemented
        return unit

        if self.baseUnit.factor == 8:  # pylint: disable=no-member
            return unit
        if self.baseUnit.factor == 5:  # pylint: disable=no-member
            return "".join({
                "m", unit[0], unit[1:].lower()
            })
        return self.baseUnit.name  # pylint: disable=no-member

    @QtCore.Property("QVariantList", constant=True)
    def rateSourceModel(self) -> "QVariantList":
        return self._rate_source_model

    @QtCore.Property(int, notify=rateSourceChanged)
    def rateSourceIndex(self) -> int:
        return self._rate_source_index

    @rateSourceIndex.setter
    def _set_rate_source_index(self, index: int) -> None:
        if index == self._rate_source_index:
            return
        self._rate_source_index = index
        self.rateSourceChanged.emit()
        self._rate_source_model[index].activate()
        self._gcd.retrieve_coin_rates()

    @QtCore.Property(rate_source.RateSource, notify=rateSourceChanged)
    def rateSource(self) -> rate_source.RateSource:
        if self._rate_source_index < len(self._rate_source_model):
            return self._rate_source_model[self._rate_source_index]

    @QtCore.Property(bool, notify=newAddressChanged)
    def newAddressFroLeftover(self) -> bool:
        return self._use_new_address

    @newAddressFroLeftover.setter
    def _set_use_new_address(self, on: bool) -> None:
        if on == self._use_new_address:
            return
        self._use_new_address = on
        self.newAddressChanged.emit()

    @QtCore.Property("QVariantMap", constant=True)
    def fontData(self) -> dict:
        return self._font_settings

    def set_font_from_hex(self, font: str) -> None:
        # we don't want notify here 'cause we rely it happens before QML loading
        if font:
            self._font_settings = pickle.loads(bytes.fromhex(font))
            log.warning(f"new font data: {self._font_settings}")

    @fontData.setter
    def _set_font_data(self, font: dict) -> None:
        self._font_settings = font
        self._gcd.save_meta("font", pickle.dumps(font).hex())
        # log.warning(f"new font data: {font}")
