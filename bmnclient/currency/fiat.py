from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

from .currency import Currency
from ..config import ConfigKey, ConfigStaticList

if TYPE_CHECKING:
    from typing import Final, Iterator, Optional, Type, Union
    from ..application import CoreApplication


class FiatCurrency(Currency):
    _DECIMAL_SIZE = (2, 2)


class NoneFiatCurrency(FiatCurrency):
    _FULL_NAME: Final = QObject().tr("-- None --")
    _UNIT: Final = "N/A"


class UsdFiatCurrency(FiatCurrency):
    _FULL_NAME: Final = QObject().tr("US Dollar")
    _UNIT: Final = "USD"


class EuroFiatCurrency(FiatCurrency):
    _FULL_NAME: Final = QObject().tr("Euro")
    _UNIT: Final = "EUR"


class FiatCurrencyList(ConfigStaticList):
    def __init__(self, application: CoreApplication) -> None:
        super().__init__(
            application.config,
            ConfigKey.SERVICES_FIAT_CURRENCY,
            (
                UsdFiatCurrency,
                EuroFiatCurrency
            ),
            default_index=0,
            item_property="unit")
        self._logger.debug(
            "Current fiat currency is '%s'.",
            self.current.unit)

    def __iter__(self) -> Iterator[Type[FiatCurrency]]:
        return super().__iter__()

    def __getitem__(
            self,
            value: Union[str, int]) -> Optional[Type[FiatCurrency]]:
        return super().__getitem__(value)

    @property
    def current(self) -> Type[FiatCurrency]:
        return super().current
