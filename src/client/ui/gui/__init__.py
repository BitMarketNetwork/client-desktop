

import logging
from typing import List
import os
import PySide2.QtCore as qt_core
import PySide2.QtQuick as qt_quick
import PySide2.QtQml as qt_qml
import PySide2.QtWidgets as qt_widgets
import qrc


# load resources
from . import api
from . import app
from . import tx_controller
from .. import AppBase

log = logging.getLogger(__name__)


class RootBase(AppBase):
    def __init__(self, gcd):
        super().__init__()
        self.api = api.Api(gcd)

    def _register(self, cxt: qt_qml.QQmlContext):
        '''
        important point here
        we'll be able to switch launching from rcc either filesystem
        it's very convenient on debug
        '''
        qml_root = 'qrc:/qml/'
        cxt.setBaseUrl(qml_root)
        cxt.setContextObject(self.api)


class RootApp(RootBase, qt_qml.QQmlApplicationEngine, ):
    serverInfo = qt_core.Signal()

    def __init__(self, gcd, parent=None):

        self.app = app.GuiApplication("XEM")
        self.app.aboutToQuit.connect(self._app_about_quit)
        super().__init__(gcd)
        gcd.reloadQml.connect(self.reload, qt_core.Qt.QueuedConnection)
        self.api.updateTr.connect(
            self._retranslate)  # pylint: disable=no-member
        # styles = qt_widgets.QStyleFactory.keys()
        # log.debug(f"supported UI styles: {styles}")
        self._engine = qt_qml.QQmlApplicationEngine(self)
        self._engine.exit.connect(self._on_exit)
        self._engine.objectCreated.connect(self._object_created)
        qt_qml.qmlRegisterType(tx_controller.TxController,
                               "Bmn", 1, 0, "TxController")

    def _on_exit(self, code: int):
        # leave it for a while
        log.debug("qml exit: {code}")

    def _app_about_quit(self):
        log.debug("app is gonna quit:")
        self._engine.deleteLater()

    def run(self, style: str):
        # if self._engine:
        #    self._engine.deleteLater()
        # self._engine.warnings.connect(self._process_qml_errors)
        os.environ["QT_QUICK_CONTROLS_STYLE"] = style or "XEM"
        self._register(self._engine.rootContext())
        self._engine.load(
            self._engine.rootContext().resolvedUrl('RootApp.qml'))
        # if not self._engine.rootObjects(): raise SystemExit(1)

    def _process_qml_errors(self, warnings: List[qt_qml.QQmlError]):
        pass

    def _object_created(self, object, url):
        log.debug(f"Loaded qml object:{url}")
        if not object:
            raise SystemExit(1)

    def reload(self):
        self._engine = qt_qml.QQmlApplicationEngine(self)
        self.run("XEM")

    def exec_(self):
        return self.app.exec_()

    @qt_core.Slot(str, str)
    def output_info(self, key, value):
        print(key, value)

    def _retranslate(self):
        log.debug(f"retranslating UI")
        self._engine.retranslate()

def run(gcd):
    root = RootApp(gcd)
    return root
