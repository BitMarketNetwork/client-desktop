

import locale
import logging
import math
import pickle
from typing import Optional, Union

import PySide2.QtCore as qt_core

from ...wallet import base_unit, coins, currency, language, rate_source, style
from . import api, settings_manager_impl

log = logging.getLogger(__name__)


class SettingsManager(settings_manager_impl.SettingsManagerImpl):
    newAddressChanged = qt_core.Signal()
    rateSourceChanged = qt_core.Signal()
    currencyChanged = qt_core.Signal()
    languageChanged = qt_core.Signal()
    styleChanged = qt_core.Signal()
    unitChanged = qt_core.Signal()

    def __init__(self, parent):
        super().__init__(parent)

    @qt_core.Slot(result=bool)
    def accept(self) -> bool:
        log.debug("Accepting settings")
        self.parent().coinManager.update_coin_model()
        self._gcd.save_coins_settings()
        return True

    @qt_core.Property("QVariantList", constant=True)
    def styleModel(self) -> "QVariantList":
        return self._style_model

    @qt_core.Property(int, notify=styleChanged)
    def styleIndex(self) -> int:
        return self._style_index

    @styleIndex.setter
    def _set_style(self, style_: Union[int, str]):
        if isinstance(style_, int):
            if style_ == self._style_index:
                return
            self._style_index = style_
            self._gcd.save_meta("style", self._style_model[style_].name)
        else:
            index = next(
                (i for i, s in enumerate(self._style_model) if s.name == style_),
                None
            )
            if index is None:
                return
            self._style_index = index
        self.styleChanged.emit()

    @qt_core.Property("QVariantList", constant=True)
    def currencyModel(self) -> "QVariantList":
        return self._currency_model

    @qt_core.Property(int, notify=currencyChanged)
    def currencyIndex(self) -> int:
        return self._currency_index

    @currencyIndex.setter
    def _set_currency(self, index: int):
        if index == self._currency_index:
            return
        self._currency_index = index
        self.currencyChanged.emit()

    @qt_core.Property(currency.Currency, notify=currencyChanged)
    def currency(self) -> currency.Currency:
        if self._currency_index < len(self._currency_model):
            return self._currency_model[self._currency_index]

    @qt_core.Property("QVariantList", constant=True)
    def unitModel(self) -> "QVariantList":
        return self._unit_model

    @qt_core.Property(int, notify=unitChanged)
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

    @qt_core.Property(base_unit.BaseUnit, notify=unitChanged)
    def baseUnit(self) -> base_unit.BaseUnit:
        if self._unit_index < len(self._unit_model):
            return self._unit_model[self._unit_index]

    @qt_core.Slot(float, result=str)
    def coinBalance(self, amount: float) -> str:
        # TODO: we disgard coin convertion ratio & decimal level !!! it's normal for btc & lts but isn't sure for next coins
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
            res = format(round(res, max(0, 2 - int(math.log10(res)))), 'f')
            if '.' in res:
                return res.rstrip("0.") or "0"
        except ValueError as ve:
            raise ValueError(f"{ve} for {amount} and {res}") from ve
        except OverflowError as oe:
            log.error(f"Overflow {amount}")
            raise OverflowError(f"{oe} for {res}") from oe

    @qt_core.Slot(str, result=str)
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

    @qt_core.Property("QVariantList", constant=True)
    def rateSourceModel(self) -> "QVariantList":
        return self._rate_source_model

    @qt_core.Property(int, notify=rateSourceChanged)
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

    @qt_core.Property(rate_source.RateSource, notify=rateSourceChanged)
    def rateSource(self) -> rate_source.RateSource:
        if self._rate_source_index < len(self._rate_source_model):
            return self._rate_source_model[self._rate_source_index]

    @qt_core.Property(bool, notify=newAddressChanged)
    def newAddressFroLeftover(self) -> bool:
        return self._use_new_address

    @newAddressFroLeftover.setter
    def _set_use_new_address(self, on: bool) -> None:
        if on == self._use_new_address:
            return
        self._use_new_address = on
        self.newAddressChanged.emit()

    @qt_core.Property("QVariantList", constant=True)
    def languageModel(self) -> "QVariantList":
        return self._language_model

    @qt_core.Property(int, notify=languageChanged)
    def languageIndex(self) -> int:
        return self._language_index

    @qt_core.Property(language.Language, notify=languageChanged)
    def language(self) -> language.Language:
        if self._language_index < len(self._language_model):
            return self._language_model[self._language_index]

    @languageIndex.setter
    def _set_language_index(self, index: int) -> None:
        if index == self._language_index or index is None:
            return
        self._language_index = index
        self.languageChanged.emit()

    def set_language(self, src: Optional[str]) -> None:
        """
        set by locale tag
        use system locale if None
        """
        if not src:
            # TODO: use english for a while
            # loc, _ = locale.getdefaultlocale()
            loc = "en"
            log.info(f"System locale is: {loc}")
            src = loc[:2]
        self._set_language_index(next(
            (i for i, l in enumerate(self._language_model) if l.locale == src), None)
        )

    @qt_core.Property("QVariantMap", constant=True)
    def fontData(self) -> dict:
        return self._font_settings

    def set_font_from_hex(self, font: str) -> None:
        # we don't want notify here 'cause we rely it happens before QML loading
        if font:
            self._font_settings = pickle.loads(bytes.fromhex(font))
            log.warning(f"new font data: {self._font_settings }")

    @fontData.setter
    def _set_font_data(self, font: dict) -> None:
        self._font_settings = font
        self._gcd.save_meta("font", pickle.dumps(font).hex())
        # log.warning(f"new font data: {font}")
