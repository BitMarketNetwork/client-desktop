import logging
import math
import pickle
from typing import Optional, Union
from bmnclient import gcd

from PySide2.QtCore import QObject, Signal as QSignal, Slot as QSlot, \
    Property as QProperty

from ...config import UserConfig
from ...wallet import base_unit, currency, rate_source
from ...language import Language

log = logging.getLogger(__name__)


class SettingsManager(QObject):
    newAddressChanged = QSignal()
    rateSourceChanged = QSignal()
    currencyChanged = QSignal()
    unitChanged = QSignal()

    def __init__(self, user_config: UserConfig) -> None:
        super().__init__()
        self._gcd = gcd.GCD.get_instance()
        self._use_new_address = True
        self._font_settings = {}
        #
        self._currency_model = []
        self._currency_index = 0
        self._fill_currencies()
        #
        self._rate_source_model = []
        self._rate_source_index = 0
        self._fill_rate_source()
        #
        self._unit_model = []
        self._unit_index = 0
        self._fill_units()

        self._user_config = user_config
        self._language_list = None
        self._current_language_name = None
        self._current_theme_name = None
        self._hide_to_tray = None

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

    def _fill_units(self):
        units = [
            ("BTC", 8),
            ("mBtc", 5),
            ("bits", 2),
            ("sat", 0),
        ]
        self._unit_model = [
            base_unit.BaseUnit(
                *val,
                self,
            )
            for val in units
        ]

    def _fill_rate_source(self):
        self._rate_source_model = [
            rate_source.RateSource(
                self,
                name=name,
            ) for name, _ in rate_source.SOURCE_OPTIONS.items()
        ]

    @QSlot(result=bool)
    def accept(self) -> bool:
        log.debug("Accepting settings")
        self.parent().coinManager.update_coin_model()
        self._gcd.save_coins_settings()
        return True

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
            name = self._user_config.get(
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
    def _setCurrentLanguageName(self, name) -> None:
        assert type(name) is str
        if not self._isValidLanguageName(name):
            log.error(f"Unknown language \"{name}\".")
            return
        self._user_config.set(UserConfig.KEY_UI_LANGUAGE, name)
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
            self._current_theme_name = self._user_config.get(
                UserConfig.KEY_UI_THEME,
                str,
                ""  # QML controlled
            )
        assert type(self._current_theme_name) is str
        return self._current_theme_name

    @currentThemeName.setter
    def _setCurrentThemeName(self, name) -> None:
        assert type(name) is str
        self._user_config.set(UserConfig.KEY_UI_THEME, name)
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
            self._hide_to_tray = self._user_config.get(
                UserConfig.KEY_UI_HIDE_TO_TRAY,
                bool,
                False)
        assert type(self._hide_to_tray) is bool
        return self._hide_to_tray

    @hideToTray.setter
    def _setHideToTray(self, value) -> None:
        assert type(value) is bool
        self._user_config.set(UserConfig.KEY_UI_HIDE_TO_TRAY, value)
        if value != self._hide_to_tray:
            self._hide_to_tray = value
            self.hideToTrayChanged.emit()

    ############################################################################
    # Font
    ############################################################################

    @QProperty("QVariantMap", constant=True)
    def fontData(self) -> dict:
        return self._font_settings

    @fontData.setter
    def _set_font_data(self, font: dict) -> None:
        self._font_settings = font
        self._gcd.save_meta("font", pickle.dumps(font).hex())

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

    @QProperty("QVariantList", constant=True)
    def unitModel(self):
        return self._unit_model

    @QProperty(int, notify=unitChanged)
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

    @QProperty(base_unit.BaseUnit, notify=unitChanged)
    def baseUnit(self) -> base_unit.BaseUnit:
        if self._unit_index < len(self._unit_model):
            return self._unit_model[self._unit_index]

    @QSlot(float, result=str)
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

    @QSlot(str, result=str)
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

    @QProperty("QVariantList", constant=True)
    def rateSourceModel(self) -> "QVariantList":
        return self._rate_source_model

    @QProperty(int, notify=rateSourceChanged)
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

    @QProperty(rate_source.RateSource, notify=rateSourceChanged)
    def rateSource(self) -> rate_source.RateSource:
        if self._rate_source_index < len(self._rate_source_model):
            return self._rate_source_model[self._rate_source_index]

    @QProperty(bool, notify=newAddressChanged)
    def newAddressFroLeftover(self) -> bool:
        return self._use_new_address

    @newAddressFroLeftover.setter
    def _set_use_new_address(self, on: bool) -> None:
        if on == self._use_new_address:
            return
        self._use_new_address = on
        self.newAddressChanged.emit()
