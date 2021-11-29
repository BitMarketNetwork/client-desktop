from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import \
    QCoreApplication, \
    QDir, \
    QDirIterator, \
    QLocale, \
    QTranslator

from .logger import Logger
from .resources import Resources
from .utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Dict, Final, List, Optional, Tuple
    TranslationList = Tuple[Dict[str, str], ...]


# QLocale: problems with negative numbers
class Locale(QLocale):
    def floatToString(self, value: float, precision: int = 2) -> str:
        if value < 0:
            value = abs(value)
            result = self.negativeSign()
        else:
            result = ""
        # noinspection PyTypeChecker
        return result + self.toString(value, "f", precision)

    def stringToFloat(
            self,
            value: str,
            *,
            strict: bool = True) -> Optional[float]:
        if strict:
            s = (self.groupSeparator(), self.decimalPoint())
            for v in value:
                if not v.isnumeric() and v not in s:
                    return None
        (value, ok) = self.toDouble(value)
        return value if ok else None

    def integerToString(self, value: int) -> str:
        if value < 0:
            value = abs(value)
            return self.negativeSign() + self.toString(value)
        return self.toString(value)

    def stringToInteger(
            self,
            value: str,
            *,
            strict: bool = True) -> Optional[int]:
        if strict:
            s = self.groupSeparator()
            for v in value:
                if not v.isnumeric() and v != s:
                    return None
        (value, ok) = self.toLongLong(value)
        return value if ok else None


class Language:
    _SUFFIX_LIST: Final = (".qm", )
    _FILE_MATH: Final = "*.qm"
    _PRIMARY_NAME: Final = "en_US"

    def __init__(self, name: str = _PRIMARY_NAME) -> None:
        self._locale = Locale() if name is None else Locale(name)
        self._logger = Logger.classLogger(
            self.__class__,
            (None, self._locale.name()))
        self._translator_list: List[QTranslator] = []
        if name != self._PRIMARY_NAME:
            for suffix in self._SUFFIX_LIST:
                translator = self._createTranslator(self._locale, suffix)
                if translator is not None:
                    self._translator_list.append(translator)

    @classproperty
    def primaryName(cls) -> str:  # noqa
        return cls._PRIMARY_NAME

    @property
    def translatorList(self) -> List[QTranslator]:
        return self._translator_list

    @property
    def name(self) -> str:
        return self._locale.name()

    @property
    def locale(self) -> Locale:
        return self._locale

    def install(self) -> bool:
        translated = False
        for translator in self._translator_list:
            if translator.isEmpty():
                self._logger.warning(
                    "Translator file '%s' is empty.",
                    translator.filePath())
                translated = True
            elif not QCoreApplication.installTranslator(translator):
                self._logger.error(
                    "Can't install translator file '%s'.",
                    translator.filePath())
            else:
                translated = True
        return translated

    def uninstall(self) -> None:
        for translator in self._translator_list:
            if not translator.isEmpty():
                QCoreApplication.removeTranslator(translator)

    @classmethod
    @lru_cache()
    def translationList(cls) -> TranslationList:
        result = [cls._appendTranslationItem(cls._PRIMARY_NAME)]
        it = QDirIterator(
            str(Resources.translationsPath),
            (cls._FILE_MATH, ),
            QDir.Files)
        while it.next():
            name = Path(it.fileName()).with_suffix('').with_suffix('').stem
            result.append(cls._appendTranslationItem(name))
        result.sort(key=lambda x: x["name"])
        return tuple(result)

    @staticmethod
    def _appendTranslationItem(name: str) -> Dict[str, str]:
        locale = Locale(name)
        assert locale.name() == name
        return {
            "name": name,
            "fullName": "{} - {}".format(
                locale.nativeLanguageName().title(),
                Locale.languageToString(locale.language()).title())
        }

    @classmethod
    def _createTranslator(
            cls,
            locale: Locale,
            suffix: str) -> Optional[QTranslator]:
        translator = QTranslator()
        result = translator.load(
            locale,
            "",
            "",
            str(Resources.translationsPath),
            suffix)

        if not result:
            Logger.classLogger(cls).error(
                "Failed to load translator: locale '{}', suffix '{}'."
                .format(locale.name(), suffix))
            return None
        return translator
