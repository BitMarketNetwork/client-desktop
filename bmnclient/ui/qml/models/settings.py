from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtCore import \
    Property as QProperty, \
    QObject, \
    Signal as QSignal

from . import AbstractModel, AbstractStateModel, AbstractTupleStateModel
from ....config import ConfigKey
from ....language import Language
from ....version import Gui

if TYPE_CHECKING:
    from typing import Any, Dict, TypedDict
    from .. import QmlApplication


class FiatRateServiceModel(AbstractTupleStateModel):
    def __init__(self, application: QmlApplication) -> None:
        super().__init__(
            application,
            tuple(
                {"name": v.name, "fullName": v.fullName}
                for v in application.fiatRateServiceList
            ))

    def _getCurrentItemName(self) -> str:
        return self._application.fiatRateServiceList.current.name

    def _setCurrentItemName(self, value: str) -> bool:
        if self._application.fiatRateServiceList.setCurrent(value):
            self._application.networkQueryScheduler.updateCurrentFiatCurrency()
            return True
        return False


class FiatCurrencyModel(AbstractTupleStateModel):
    def __init__(self, application: QmlApplication) -> None:
        super().__init__(
            application,
            tuple(
                {
                    "name": v.unit,
                    "fullName": "{} ({})".format(v.fullName, v.unit)
                } for v in application.fiatCurrencyList
            ))

    def _getCurrentItemName(self) -> str:
        return self._application.fiatCurrencyList.current.unit

    def _setCurrentItemName(self, value: str) -> bool:
        if self._application.fiatCurrencyList.setCurrent(value):
            self._application.networkQueryScheduler.updateCurrentFiatCurrency()
            return True
        return False


class LanguageModel(AbstractTupleStateModel):
    def __init__(self, application: QmlApplication) -> None:
        super().__init__(
            application,
            Language.translationList(),
            config_key=ConfigKey.UI_LANGUAGE,
            default_name=Language.primaryName)

    def _setCurrentItemName(self, value: str) -> bool:
        if super()._setCurrentItemName(value):
            self._application.updateTranslation()
            return True
        return False


class ThemeModel(AbstractTupleStateModel):
    def __init__(self, application: QmlApplication) -> None:
        super().__init__(
            application,
            tuple(),  # QML controlled
            config_key=ConfigKey.UI_THEME,
            default_name=Gui.DEFAULT_THEME_NAME)

    def _isValidName(self, name) -> bool:
        return True if name else False


class FontModel(AbstractStateModel):
    __stateChanged = QSignal()

    if TYPE_CHECKING:
        # QML Qt.font() comfortable
        class FontDict(TypedDict):
            family: str
            pointSize: int

    def __init__(self, application: QmlApplication) -> None:
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
        with self._application.config.lock:
            family = self._application.config.get(
                ConfigKey.UI_FONT_FAMILY,
                str,
                "")
            if not family:
                family = self._default_font["family"]
            point_size = self._application.config.get(
                ConfigKey.UI_FONT_SIZE,
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

        with self._application.config.lock:
            self._application.config.set(
                ConfigKey.UI_FONT_FAMILY,
                family,
                save=False)
            self._application.config.set(
                ConfigKey.UI_FONT_SIZE,
                point_size,
                save=False)
            self._application.config.save()

        value: FontModel.FontDict = dict(family=family, pointSize=point_size)
        if self._font != value:
            self._font = value
            self.update()


class SystemTrayModel(AbstractStateModel):
    __stateChanged = QSignal()

    def __init__(self, application: QmlApplication) -> None:
        super().__init__(application)
        self._close_to_tray = self._application.config.get(
            ConfigKey.UI_CLOSE_TO_TRAY,
            bool,
            False)

    @QProperty(bool, notify=__stateChanged)
    def closeToTray(self) -> bool:
        return self._close_to_tray

    @closeToTray.setter
    def _setCloseToTray(self, value: bool) -> None:
        value = bool(value)
        self._application.config.set(
            ConfigKey.UI_CLOSE_TO_TRAY,
            value)
        if self._close_to_tray != value:
            self._close_to_tray = value
            self.update()


class SettingsModel(AbstractModel):
    def __init__(self, application: QmlApplication) -> None:
        super().__init__(application)

        self._fiat_rate_service_model = FiatRateServiceModel(self._application)
        self._fiat_currency_service_model = FiatCurrencyModel(self._application)
        self._language_model = LanguageModel(self._application)
        self._theme_model = ThemeModel(self._application)
        self._font_model = FontModel(self._application)
        self._system_tray_model = SystemTrayModel(self._application)

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
