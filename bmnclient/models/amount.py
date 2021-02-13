# JOK++
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Callable, Final, Optional, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, Signal as QSignal, \
    Slot as QSlot
from PySide2.QtGui import QValidator

if TYPE_CHECKING:
    from ..wallet.coins import CoinType
    from ..ui.gui import Application
    from ..coins.currency import AbstractCurrency


class AmountModel(
        QObject,
        metaclass=type('AmountModelMeta', (ABCMeta, type(QObject)), {})):
    _stateChanged: Final = QSignal()

    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__()
        self._application = application
        self._coin = coin

    @abstractmethod
    def _getValue(self) -> int:
        raise NotImplementedError

    def refresh(self) -> None:
        self._stateChanged.emit()

    @QProperty(str, notify=_stateChanged)
    def value(self) -> int:
        return self._getValue()

    @QProperty(str, notify=_stateChanged)
    def valueHuman(self) -> str:
        return self._coin.currency.toString(
            self._getValue(),
            locale=self._application.language.locale)

    @QProperty(str, constant=True)
    def unit(self) -> str:
        return self._coin.currency.unit

    @QProperty(str, notify=_stateChanged)
    def fiatValueHuman(self) -> str:
        return self._coin.fiatRate.currency.toString(
            self._coin.toFiatAmount(self._getValue()),
            locale=self._application.language.locale)

    @QProperty(str, notify=_stateChanged)
    def fiatUnit(self) -> str:
        return self._coin.fiatRate.currency.unit


class AmountInputModel(AmountModel, metaclass=ABCMeta):
    _stateChanged2: Final = QSignal()

    class _Validator(QValidator):
        def __init__(self, owner: AmountInputModel):
            super().__init__()
            self._owner = owner

        def _normalizeValue(self, value: str) -> str:
            value = value.replace(
                self._owner._application.language.locale.groupSeparator(),
                '')
            if value and value[0] in (
                    "+",
                    "-",
                    self._owner._application.language.locale.positiveSign(),
                    self._owner._application.language.locale.negativeSign()):
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

            value = currency.fromString(
                value,
                strict=False,
                locale=self._owner._application.language.locale)
            if value is not None:
                if not unit_convert or unit_convert(value) is not None:
                    return QValidator.State.Acceptable
            return QValidator.State.Invalid

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
    def _setValue(self, value: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _setMaxValue(self) -> None:
        raise NotImplementedError

    def _setValueHelper(
            self,
            value: str,
            currency: AbstractCurrency,
            unit_convert: Optional[Callable[[int], int]] = None) -> bool:
        if not value:
            value = 0
        else:
            value = currency.fromString(
                value,
                strict=False,
                locale=self._application.language.locale)
            if value is None:
                return False

        if unit_convert:
            value = unit_convert(value)
            if value is None:
                return False

        if value != self._getValue():
            if not self._setValue(value):
                return False
            self.refresh()
        return True

    def refresh(self) -> None:
        super().refresh()
        self._stateChanged2.emit()

    @QProperty(QValidator, constant=True)
    def valueHumanValidator(self) -> QValidator:
        return self._value_human_validator

    @QProperty(QValidator, notify=_stateChanged2)
    def fiatValueHumanValidator(self) -> QValidator:
        return self._fiat_value_human_validator

    @QProperty(str, notify=_stateChanged2)
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
    def setMaxValue(self) -> bool:
        self._setMaxValue()
        self.refresh()
        return True
