# JOK
import logging
from pathlib import PurePath
from typing import Optional, List

from PySide2 import QtCore

import bmnclient.version


class Language:
    _logger = logging.getLogger(__name__)
    SUFFIX_LIST = (".qml.qm", ".py.qm",)
    FILE_MATH = "*.qml.qm"
    PRIMARY_NAME = "en_US"

    def __init__(self, name=PRIMARY_NAME) -> None:
        self._logger = logging.getLogger(__name__ + "-" + name)

        if name is None:
            self._locale = QtCore.QLocale()
        else:
            self._locale = QtCore.QLocale(name)

        self._translator_list = []
        if name != Language.PRIMARY_NAME:
            for suffix in Language.SUFFIX_LIST:
                translator = Language._createTranslator(self._locale, suffix)
                if translator is not None:
                    self._translator_list.append(translator)

    @property
    def translatorList(self) -> List[QtCore.QTranslator]:
        return self._translator_list

    @property
    def name(self) -> str:
        return self._locale.name()

    def install(self) -> bool:
        translated = False
        for translator in self._translator_list:
            if translator.isEmpty():
                self._logger.warning(
                    "Translator file \"{}\" is empty."
                    .format(translator.filePath()))
            elif not QtCore.QCoreApplication.installTranslator(translator):
                self._logger.error(
                    "Can't install translator file \"{}\"."
                    .format(translator.filePath()))
            else:
                translated = True
        return translated

    def uninstall(self) -> None:
        for translator in self._translator_list:
            if not translator.isEmpty():
                QtCore.QCoreApplication.removeTranslator(translator)

    @staticmethod
    def createTranslationList() -> List[dict]:
        result = [
            Language._createAvailableTranslationItem(Language.PRIMARY_NAME)
        ]
        it = QtCore.QDirIterator(
            str(bmnclient.version.TRANSLATIONS_PATH),
            (Language.FILE_MATH, ),
            QtCore.QDir.Files)
        while it.next():
            name = PurePath(it.fileName()).with_suffix('').with_suffix('').stem
            result.append(Language._createAvailableTranslationItem(name))
        result.sort(key=lambda x: x["name"])
        return result

    @staticmethod
    def _createAvailableTranslationItem(name) -> dict:
        locale = QtCore.QLocale(name)
        assert locale.name() == name
        return {
            "name": name,
            "friendlyName": "{} - {}".format(
                locale.nativeLanguageName().title(),
                QtCore.QLocale.languageToString(locale.language()).title())
        }

    @staticmethod
    def _createTranslator(locale, suffix) -> Optional[QtCore.QTranslator]:
        translator = QtCore.QTranslator()
        result = translator.load(
            locale,
            "",
            "",
            str(bmnclient.version.TRANSLATIONS_PATH),
            suffix)

        if not result:
            Language._logger.error(
                "Failed to load translator: "
                + "locale \"{}\", suffix \"{}\"."
                .format(locale.name(), suffix))
            return None
        return translator
