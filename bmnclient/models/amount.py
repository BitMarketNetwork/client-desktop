# JOK++
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Callable, Optional, TYPE_CHECKING, Union

from PySide2.QtCore import \
    Property as QProperty, \
    Signal as QSignal, \
    Slot as QSlot
from PySide2.QtGui import QValidator

from . import AbstractStateModel

if TYPE_CHECKING:
    from ..wallet.coins import CoinType
    from ..ui.gui import Application
    from ..coins.currency import AbstractCurrency


class AmountModel(
        AbstractStateModel,
        metaclass=type(
            'AmountModelMeta',
            (ABCMeta, type(AbstractStateModel)),
            {})):
    __stateChanged = QSignal()

    @abstractmethod
    def _getValue(self) -> Optional[int]:
        raise NotImplementedError

    def _toHumanValue(self, value: int, currency: AbstractCurrency) -> str:
        return currency.toString(value, locale=self.locale)

    @QProperty(str, notify=__stateChanged)
    def value(self) -> int:
        v = self._getValue()
        return 0 if v is None else v

    @QProperty(str, notify=__stateChanged)
    def valueHuman(self) -> str:
        return self._toHumanValue(self.value, self._coin.currency)

    @QProperty(str, constant=True)
    def unit(self) -> str:
        return self._coin.currency.unit

    @QProperty(str, notify=__stateChanged)
    def fiatValueHuman(self) -> str:
        return self._toHumanValue(
            self._coin.toFiatAmount(self.value),
            self._coin.fiatRate.currency)

    @QProperty(str, notify=__stateChanged)
    def fiatUnit(self) -> str:
        return self._coin.fiatRate.currency.unit


class AmountInputModel(AmountModel, metaclass=ABCMeta):
    __stateChanged = QSignal()

    class _Validator(QValidator):
        def __init__(self, owner: AmountInputModel):
            super().__init__()
            self._owner = owner

        def _normalizeValue(self, value: str) -> str:
            value = value.replace(
                self._owner.locale.groupSeparator(),
                '')
            if value and value[0] in (
                    "+",
                    "-",
                    self._owner.locale.positiveSign(),
                    self._owner.locale.negativeSign()):
                value = value[1:]
            return value

        def _validateHelper(
                self,
                value: str,
                currency: AbstractCurrency,
                unit_convert: Optional[Callable[[int], int]] = None) \
                -> QValidator.State:
            value = self._normalizeValue(value)
            if not value:
                return QValidator.State.Intermediate
            value = self._owner._fromHumanValue(value, currency, unit_convert)
            if value is None:
                return QValidator.State.Invalid
            return QValidator.State.Acceptable

    class _ValueHumanValidator(_Validator):
        def validate(self, value: str, _) -> QValidator.State:
            return self._validateHelper(
                value,
                self._owner._coin.currency)

    class _FiatValueHumanValidator(_Validator):
        def validate(self, value: str, _) -> QValidator.State:
            return self._validateHelper(
                value,
                self._owner._coin.fiatRate.currency,
                self._owner._coin.fromFiatAmount)

    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__(application, coin)
        self._value_human_validator = self._ValueHumanValidator(self)
        self._fiat_value_human_validator = self._FiatValueHumanValidator(self)

    @abstractmethod
    def _setValue(self, value: Optional[int]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _getDefaultValue(self) -> Optional[int]:
        raise NotImplementedError

    def _fromHumanValue(
            self,
            value: str,
            currency: AbstractCurrency,
            unit_convert: Optional[Callable[[int], Optional[int]]] = None) \
            -> Optional[int]:
        if not value:
            value = 0
        else:
            value = currency.fromString(value, strict=False, locale=self.locale)
            if value is None:
                return None

        if unit_convert:
            value = unit_convert(value)
        return value

    def _setValueHelper(
            self,
            value: Optional[Union[str, int]],
            currency: AbstractCurrency,
            unit_convert: Optional[Callable[[int], Optional[int]]] = None) \
            -> bool:
        if isinstance(value, str):
            value = self._fromHumanValue(value, currency, unit_convert)
        result = value is not None
        if value != self._getValue():
            if value is None:
                self._setValue(None)
            else:
                result = self._setValue(value)
            self.refresh()
        return result

    @QProperty(QValidator, constant=True)
    def valueHumanValidator(self) -> QValidator:
        return self._value_human_validator

    @QProperty(QValidator, notify=__stateChanged)
    def fiatValueHumanValidator(self) -> QValidator:
        return self._fiat_value_human_validator

    @QProperty(str, notify=__stateChanged)
    def valueHumanTemplate(self) -> str:
        a = self._coin.currency.stringTemplate
        b = self._coin.fiatRate.currency.stringTemplate
        return a if len(a) > len(b) else b

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def setValueHuman(self, value: str) -> bool:
        return self._setValueHelper(
            value,
            self._coin.currency)

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def setFiatValueHuman(self, value: str) -> bool:
        return self._setValueHelper(
            value,
            self._coin.fiatRate.currency,
            self._coin.fromFiatAmount)

    # noinspection PyTypeChecker
    @QSlot(result=bool)
    def setDefaultValue(self) -> bool:
        return self._setValueHelper(
            self._getDefaultValue(),
            self._coin.currency)
