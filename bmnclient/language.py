# JOK+
from pathlib import PurePath
from typing import Optional, List

from PySide2.QtCore import \
    QCoreApplication, \
    QDir, \
    QDirIterator, \
    QLocale, \
    QTranslator

from .logger import getClassLogger
from .version import Paths


class Language:
    SUFFIX_LIST = (".qml.qm", ".py.qm",)
    FILE_MATH = "*.qml.qm"
    PRIMARY_NAME = "en_US"

    def __init__(self, name: str = PRIMARY_NAME) -> None:
        self._logger = getClassLogger(__name__, self.__class__, name)

        if name is None:
            self._locale = QLocale()
        else:
            self._locale = QLocale(name)

        self._translator_list = []
        if name != self.PRIMARY_NAME:
            for suffix in self.SUFFIX_LIST:
                translator = self._createTranslator(self._locale, suffix)
                if translator is not None:
                    self._translator_list.append(translator)

    @property
    def translatorList(self) -> List[QTranslator]:
        return self._translator_list

    @property
    def name(self) -> str:
        return self._locale.name()

    def install(self) -> bool:
        translated = False
        for translator in self._translator_list:
            if translator.isEmpty():
                self._logger.warning(
                    "Translator file \"%s\" is empty.",
                    translator.filePath())
            elif not QCoreApplication.installTranslator(translator):
                self._logger.error(
                    "Can't install translator file \"%s\".",
                    translator.filePath())
            else:
                translated = True
        return translated

    def uninstall(self) -> None:
        for translator in self._translator_list:
            if not translator.isEmpty():
                QCoreApplication.removeTranslator(translator)

    @classmethod
    def createTranslationList(cls) -> List[dict]:
        result = [
            cls._createAvailableTranslationItem(cls.PRIMARY_NAME)
        ]
        it = QDirIterator(
            str(Paths.TRANSLATIONS_PATH),
            (cls.FILE_MATH,),
            QDir.Files)
        while it.next():
            name = PurePath(it.fileName()).with_suffix('').with_suffix('').stem
            result.append(cls._createAvailableTranslationItem(name))
        result.sort(key=lambda x: x["name"])
        return result

    @classmethod
    def _createAvailableTranslationItem(cls, name: str) -> dict:
        locale = QLocale(name)
        assert locale.name() == name
        return {
            "name": name,
            "friendlyName": "{} - {}".format(
                locale.nativeLanguageName().title(),
                QLocale.languageToString(locale.language()).title())
        }

    @classmethod
    def _createTranslator(
            cls,
            locale: QLocale,
            suffix: str) -> Optional[QTranslator]:
        translator = QTranslator()
        result = translator.load(
            locale,
            "",
            "",
            str(Paths.TRANSLATIONS_PATH),
            suffix)

        if not result:
            getClassLogger(__name__, cls).error(
                "Failed to load translator: locale \"{}\", suffix \"{}\"."
                .format(locale.name(), suffix))
            return None
        return translator
