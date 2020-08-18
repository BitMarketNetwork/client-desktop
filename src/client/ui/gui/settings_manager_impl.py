
import logging

import PySide2.QtCore as qt_core

import translation

from ...wallet import base_unit, coins, currency, language, rate_source, style
from ... import gcd

log = logging.getLogger(__name__)


class SettingsManagerImpl(qt_core.QObject):

    def __init__(self, parent):
        super().__init__(parent)
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
        self._language_model = []
        self._language_index = 0
        self._fill_languages()
        #
        self._style_model = []
        self._style_index = 0
        self._fill_styles()
        #
        self._unit_model = []
        self._unit_index = 0
        self._fill_units()

    def _fill_styles(self):
        # ? what else
        styles = [
            "Default",
            "Bmn",
            "Dark",
            "Dracula",
            "Fusion",
            "Universal",
            "Imagine",
            "Material",
        ]
        self._style_model = [
            style.Style(self, name=name,) for name in styles
        ]

    def _fill_languages(self):
        sources = [
            ("English", "en"),
            ("Русский", "ru"),
            # ("Français", "fr"),
            # ("Deutsche", "de"),
            # ("Español", "es"),
            # ("Portuguesa", "pt"),
            # ("Italian", "it"),
            # ("Česky", "cs"),
            # ("Polskie", "pl"),
            # ("Ελληνικά", "el"),
            # ("Български", "bg"),
            # ("Magyar", "hu"),
            ("Українська", "uk"),
            # ("Tiếng việt", "vi"),
            # ("יידיש", "yi"),
            # ("中国", "zh"),
            # ("대한민국", "ko"),
            # ("日本", "ja"),
            # ("हिन्दुस्तानी", "hi"),
            # ("العربية", "ar"),
        ]
        translations = list(translation.tr_codes())
        if len(translations) != len(sources):
            # raise SystemError(
            log.debug(
                f"Translation count mismatch. Defined:{len(sources)} != Translation count: {len(translations)}")
        self._language_model = [
            language.Language(
                self,
                name=name,
                locale=locale,
            )
            for name, locale in sources
        ]

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
