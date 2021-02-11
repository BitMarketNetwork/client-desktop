# JOK++
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Final, TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, Signal as QSignal, \
    Slot as QSlot
from PySide2.QtGui import QValidator

if TYPE_CHECKING:
    from ..wallet.coins import CoinType
    from ..ui.gui import Application


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

    @abstractmethod
    def _getFiatValue(self) -> float:
        raise NotImplementedError

    def refresh(self) -> None:
        self._stateChanged.emit()

    @QProperty(str, notify=_stateChanged)
    def value(self) -> int:
        return self._getValue()

    @QProperty(str, notify=_stateChanged)
    def valueHuman(self) -> str:
        return self._coin.amountToString(
            self._getValue(),
            locale=self._application.language.locale)

    @QProperty(str, constant=True)
    def unit(self) -> str:
        return self._coin.unit

    @QProperty(str, notify=_stateChanged)
    def fiatValueHuman(self) -> str:
        return self._application.language.locale.floatToString(
            self._getFiatValue(),
            2)

    @QProperty(str, notify=_stateChanged)
    def fiatUnit(self) -> str:
        return "USD"  # TODO


class AmountEditModel(AmountModel, metaclass=ABCMeta):
    class _Validator(QValidator):
        def __init__(self, owner: AmountEditModel):
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

    class _ValueHumanValidator(_Validator):
        def validate(self, value: str, _) -> QValidator.State:
            value = self._normalizeValue(value)
            if not value:
                return self.State.Intermediate
            value = self._owner._coin.stringToAmount(
                value,
                locale=self._owner._application.language.locale)
            if value is None:
                return self.State.Invalid
            else:
                return self.State.Acceptable

    class _FiatValueHumanValidator(_Validator):
        def validate(self, value: str, _) -> QValidator.State:
            # TODO
            if not value:
                return self.State.Invalid
            else:
                return self.State.Acceptable

    def __init__(self, application: Application, coin: CoinType) -> None:
        super().__init__(application, coin)
        self._value_human_validator = self._ValueHumanValidator(self)
        self._fiat_value_human_validator = self._FiatValueHumanValidator(self)

    @abstractmethod
    def _setValue(self, value: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _setFiatValue(self, value: float) -> bool:
        raise NotImplementedError

    @QProperty(QValidator, constant=True)
    def valueHumanValidator(self) -> QValidator:
        return self._value_human_validator

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def setValueHuman(self, value: str) -> bool:
        value = self._coin.stringToAmount(
            value,
            locale=self._application.language.locale)
        if value is None:
            return False
        if value != self._value():
            self._setValue(value)
            self.refresh()
        return True

    @QProperty(QValidator, constant=True)
    def fiatValueHumanValidator(self) -> QValidator:
        return self._fiat_value_human_validator

    # noinspection PyTypeChecker
    @QSlot(str, result=bool)
    def setFiatValueHuman(self, value: str) -> bool:
        # TODO
        return False
