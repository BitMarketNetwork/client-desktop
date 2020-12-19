
import logging

import PySide2.QtCore as qt_core
from bmnclient import gcd
from bmnclient.wallet import (base_unit, currency, rate_source)

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
        self._unit_model = []
        self._unit_index = 0
        self._fill_units()

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
