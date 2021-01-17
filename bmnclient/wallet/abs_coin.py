
import locale
import logging
import PySide2.QtCore as qt_core
from . import db_entry

"""
try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
"""

log = logging.getLogger(__name__)


class CoinBase(db_entry.DbEntry):
    rateChanged = qt_core.Signal()

    name: str = None
    _decimal_level: int = 0
    full_name: str = None
    # for web explrores
    net_name: str = None
    # it differs from self._status! the former is hardcoded but the latter depends on the server daemon
    _enabled: bool = False
    # test network or not
    _test: bool = False
    #
    _usd_rate: float = 0.
    # more stable
    _btc_rate: float = 0.
    _convertion_ratio: float = 100000000.

    def __init__(self, parent):
        super().__init__(parent)
        self._balance = 0.

    @qt_core.Property(str, constant=True)
    def unit(self) -> str:
        """
        Coin unit name
        """
        if self._test:
            return self.name[:-4].upper()
        return self.name.upper()

    @qt_core.Property(str, constant=True)
    def icon(self) -> str:
        if self._test:
            return f"coins/{self.name[:-4]}.svg"
        return f"coins/{self.name}.svg"

    @qt_core.Property(bool, constant=True)
    def enabled(self) -> bool:
        return self._enabled

    @qt_core.Property(str, constant=True)
    def fullName(self) -> str:
        return self.full_name

    @qt_core.Property(str, constant=True)
    def shortName(self) -> str:
        return self.name

    @qt_core.Property(str, constant=True)
    def netName(self) -> str:
        return self.net_name or self.name

    @qt_core.Property(int, constant=True)
    def decimalLevel(self) -> int:
        return self._decimal_level

    @classmethod
    def costs(cls, another: 'CoinBase') -> float:
        "returns how much costs ANOTHER coin in THIS coins"
        if cls == another:
            return 1.
        if hasattr(cls, "_btc_rate") and hasattr(another, "_btc_rate"):
            return another._btc_rate / cls._btc_rate
        # less accurate and stable
        if hasattr(cls, "_usd_rate") and hasattr(another, "_usd_rate"):
            return another._usd_rate / cls._usd_rate

    def balance_human(self, amount: float = None) -> str:
        if amount is None:
            amount = self._balance
        res = amount / self._convertion_ratio
        # log.debug(f"{res} == {round(res, self._decimal_level)}")
        res = format(round(res, self._decimal_level), 'f')
        if '.' in res:
            return res.rstrip("0.") or "0"
        return res

    def from_human(self, value: str) -> float:
        return float(value) * self._convertion_ratio

    def fiat_amount(self, amount: float, convert=True) -> str:
        # return locale.currency(round(amount * self._usd_rate / (self._convertion_ratio if convert else 1.), 2))
        return '${:,.2f}'.format(round(amount * self._usd_rate / (self._convertion_ratio if convert else 1.), 2))

    def _get_rate(self)-> float:
        "USD rate"
        return self._usd_rate

    def _set_rate(self, rt: float):
        if rt == self._usd_rate:
            return
        self._usd_rate = rt
        self.rateChanged.emit()

    rate = qt_core.Property(int, _get_rate, _set_rate, notify=rateChanged)
