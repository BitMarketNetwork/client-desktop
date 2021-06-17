# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING
from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal, \
    Slot as QSlot

from . import AbstractModel, AbstractStateModel

if TYPE_CHECKING:
    from typing import Optional
    from .. import GuiApplication


class FiatRateServiceModel(AbstractStateModel):
    pass


class FiatCurrencyModel(AbstractStateModel):
    pass


class LanguageModel(AbstractStateModel):
    pass


class ThemeModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__(application)
        self._current_name: Optional[str] = None

    @QProperty(str, notify=__stateChanged)
    def currentName(self) -> str:
        if self._current_name is None:
            self._current_name = self._application.userConfig.get(
                self._application.userConfig.Key.UI_THEME,
                str,
                ""  # QML controlled
            )
        return self._current_name

    @currentName.setter
    def setCurrentName(self, value: str) -> None:
        value = str(value)
        self._application.userConfig.set(
            self._application.userConfig.Key.UI_THEME,
            value)
        if self._current_name != value:
            self._current_name = value
            self.update()


class FontModel(AbstractStateModel):
    pass


class SystemTrayModel(AbstractStateModel):
    pass


class SettingsModel(AbstractModel):
    def __init__(self, application: GuiApplication) -> None:
        super().__init__(application)

        self._fiat_rate_service_model = FiatRateServiceModel(self._application)
        self.connectModelUpdate(self._fiat_rate_service_model)

        self._fiat_currency_service_model = FiatCurrencyModel(self._application)
        self.connectModelUpdate(self._fiat_currency_service_model)

        self._language_model = LanguageModel(self._application)
        self.connectModelUpdate(self._language_model)

        self._theme_model = ThemeModel(self._application)
        self.connectModelUpdate(self._theme_model)

        self._font_model = FontModel(self._application)
        self.connectModelUpdate(self._font_model)

        self._system_tray_model = SystemTrayModel(self._application)
        self.connectModelUpdate(self._system_tray_model)

    @QProperty(QObject, constant=True)
    def fiatRateService(self) -> FiatRateServiceModel:
        return self._fiat_rate_service_model

    @QProperty(QObject, constant=True)
    def fiatCurrency(self) -> FiatCurrencyModel:
        return self._fiat_currency_service_model

    @QProperty(QObject, constant=True)
    def language(self) -> LanguageModel:
        return self._language_model

    @QProperty(QObject, constant=True)
    def theme(self) -> ThemeModel:
        return self._theme_model

    @QProperty(QObject, constant=True)
    def font(self) -> FontModel:
        return self._font_model

    @QProperty(QObject, constant=True)
    def systemTray(self) -> SystemTrayModel:
        return self._system_tray_model
