
import logging
from typing import Union, List
import PySide2.QtCore as qt_core

from . import rate_source_impl, coins
log = logging.getLogger(__name__)

"""
source = [
    (
        "BitPay",
        "https://bitpay.com/tokens",
    ),
    (
        "BitcoinAverage",
        "https://bitcoinaverage.com/cryptocurrency-markets-api",
    ),
    (
        "CoinDesk",
        "https://www.coindesk.com/resources/api",
    ),
    (
        "Coinbase",
        "https://api-public.sandbox.pro.coinbase.com",
    ),
]
"""

SOURCE_OPTIONS = {
    "BitPay": rate_source_impl.CoinMarkerCapWorker,
    "CoinGecko": rate_source_impl.CoinGeckoWorker,
    "CoinLayer": rate_source_impl.CoinLayerWorker,
}


class RateSource(qt_core.QObject):

    def __init__(self, parent, name):
        super().__init__(parent=parent)
        # let it be local
        self._name = name
        self._worker = None

    @qt_core.Property(str, constant=True)
    def name(self):
        return self._name

    def activate(self):
        self._worker = SOURCE_OPTIONS[self._name]()

    @property
    def api_url(self) -> str:
        if self._worker is None:
            self.activate()
        return self._worker.api_url

    @property
    def action(self) -> str:
        if self._worker is None:
            self.activate()
        return self._worker.action

    def get_arguments(self, coins: list, currencies: Union[list, str]) -> dict:
        return self._worker.get_arguments(coins, currencies)

    def process_result(self, coins: List[coins.CoinType], currencies: Union[list, str], table: dict) -> None:
        # log.debug(f"coins:{coins} fiat:{currencies} table:{table}")
        return self._worker.process_result(coins, currencies, table)

    def __str__(self):
        return f"{self._name}"
