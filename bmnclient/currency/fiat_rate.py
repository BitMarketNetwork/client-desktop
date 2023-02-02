from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type
    from .fiat import FiatCurrency


class FiatRate:
    def __init__(self, value: int, currency_type: Type[FiatCurrency]) -> None:
        self._value = value
        self._currency_type = currency_type

    def __eq__(self, other: FiatRate) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._value == other._value
                and self._currency_type is other._currency_type)

    def __hash__(self) -> int:
        return hash((self._value, ))

    @property
    def value(self) -> int:
        return self._value

    @property
    def currencyType(self) -> Type[FiatCurrency]:
        return self._currency_type
