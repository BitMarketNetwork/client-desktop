# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal

from . import AbstractModel, AbstractStateModel
from ....language import Language
from ....version import Gui

if TYPE_CHECKING:
    from typing import Any, Dict, TypedDict
    from .. import GuiApplication
    from ....language import TranslationList


class FiatRateServiceModel(AbstractStateModel):
    pass


class FiatCurrencyModel(AbstractStateModel):
    pass


class LanguageModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__(application)
        self._list = Language.translationList()
        self._current_name = self._application.userConfig.get(
            self._application.userConfig.Key.UI_LANGUAGE,
            str,
            Language.primaryName)
        if not self._isValidName(self._current_name):
            self._current_name = Language.primaryName

    @QProperty(list, constant=True)
    def list(self) -> TranslationList:
        return self._list

    def _isValidName(self, name) -> bool:
        if name:
            for language in self._list:
                if name == language["name"]:
                    return True
        return False

    @QProperty(str, notify=__stateChanged)
    def currentName(self) -> str:
        return self._current_name

    @currentName.setter
    def _setCurrentName(self, value: str) -> None:
        if not self._isValidName(value):
            return
        self._application.userConfig.set(
            self._application.userConfig.Key.UI_LANGUAGE,
            value)
        if self._current_name != value:
            self._current_name = value
            self.update()


class ThemeModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__(application)
        self._current_name = self._application.userConfig.get(
            self._application.userConfig.Key.UI_THEME,
            str,
            "")  # QML controlled

    @QProperty(str, notify=__stateChanged)
    def currentName(self) -> str:
        return self._current_name

    @currentName.setter
    def _setCurrentName(self, value: str) -> None:
        if not value:
            return
        self._application.userConfig.set(
            self._application.userConfig.Key.UI_THEME,
            value)
        if self._current_name != value:
            self._current_name = value
            self.update()


class FontModel(AbstractStateModel):
    __stateChanged = QSignal()

    if TYPE_CHECKING:
        # QML Qt.font() comfortable
        class FontDict(TypedDict):
            family: str
            pointSize: int

    def __init__(self, application: GuiApplication) -> None:
        super().__init__(application)
        self._default_font = self.__defaultFont()
        self._font = self.__currentFont()

    def __defaultFont(self) -> FontDict:
        font = self._application.defaultFont
        family = font.family()
        point_size = font.pointSize()
        if point_size <= 0:
            point_size = Gui.DEFAULT_FONT_POINT_SIZE
        return dict(family=family, pointSize=point_size)

    def __currentFont(self) -> FontDict:
        with self._application.userConfig.lock:
            family = self._application.userConfig.get(
                self._application.userConfig.Key.UI_FONT_FAMILY,
                str,
                "")
            if not family:
                family = self._default_font["family"]
            point_size = self._application.userConfig.get(
                self._application.userConfig.Key.UI_FONT_SIZE,
                int,
                0)
            if point_size <= 0:
                point_size = self._default_font["pointSize"]
        return dict(family=family, pointSize=point_size)

    # noinspection PyTypeChecker
    @QProperty("QVariantMap", notify=__stateChanged)
    def current(self) -> FontDict:
        return self._font

    @current.setter
    def _setCurrent(self, value: Dict[str, Any]) -> None:
        family = str(value.get("family", ""))
        if not family:
            family = self._default_font["family"]
        point_size = int(value.get("pointSize", 0))
        if point_size <= 0:
            point_size = self._default_font["pointSize"]

        with self._application.userConfig.lock:
            self._application.userConfig.set(
                self._application.userConfig.Key.UI_FONT_FAMILY,
                family,
                save=False)
            self._application.userConfig.set(
                self._application.userConfig.Key.UI_FONT_SIZE,
                point_size,
                save=False)
            self._application.userConfig.save()

        value: FontModel.FontDict = dict(family=family, pointSize=point_size)
        if self._font != value:
            self._font = value
            self.update()


class SystemTrayModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: GuiApplication) -> None:
        super().__init__(application)
        self._close_to_tray = self._application.userConfig.get(
            self._application.userConfig.Key.UI_CLOSE_TO_TRAY,
            bool,
            False)

    @QProperty(bool, notify=__stateChanged)
    def closeToTray(self) -> bool:
        return self._close_to_tray

    @closeToTray.setter
    def _setCloseToTray(self, value: bool) -> None:
        value = bool(value)
        self._application.userConfig.set(
            self._application.userConfig.Key.UI_CLOSE_TO_TRAY,
            value)
        if self._close_to_tray != value:
            self._close_to_tray = value
            self.update()


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
