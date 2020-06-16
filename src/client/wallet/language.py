
import logging
import PySide2.QtCore as qt_core
import translation
log = logging.getLogger(__name__)


class Language(qt_core.QObject):

    def __init__(self, parent, **kwargs):
        super().__init__(parent=parent)
        self._name = kwargs["name"]
        self._locale_string = kwargs["locale"]

    @qt_core.Property(str, constant=True)
    def name(self) -> str:
        return self._name

    @qt_core.Property(str, constant=True)
    def locale(self) -> str:
        return self._locale_string

    @property
    def qml_translator(self) -> qt_core.QTranslator:
        return self._translator(True)

    @property
    def py_translator(self)-> qt_core.QTranslator:
        return self._translator(False)

    def _translator(self, qml: bool) -> qt_core.QTranslator:
        key = "qml" if qml else "py"
        try:
            return getattr(self, key)
        except AttributeError:
            trans = qt_core.QTranslator()
            filename = translation.binary_path(key, self.locale)
            log.info(f"loading '{key}' locale: {self.locale} from {filename}")
            if trans.load(filename):
                setattr(self, key, trans)
            else:
                log.error(f"can't load tr binary:{filename}")
        return getattr(self, key, None)

    def __str__(self) -> str:
        return f"{self._name}: {self._locale_string}"
