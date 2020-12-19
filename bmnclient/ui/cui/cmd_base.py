import sys
import logging
import cmd
import PySide2.QtCore as qt_core
from bmnclient import gcd
from bmnclient.wallet import address

import bmnclient.version as e_config_version

log = logging.getLogger(__name__)


class ConsoleInputError(Exception):
    pass


class Input(qt_core.QObject):
    prompt = f'({e_config_version.SHORT_NAME}) '
    input = qt_core.Signal(str, arguments="line")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = qt_core.QBasicTimer()
        self._timer.start(10, self)

    def timerEvent(self, te):
        sys.stdout.write(self.prompt)
        sys.stdout.flush()
        line = sys.stdin.readline()
        if not len(line):
            line = 'EOF'
        else:
            line = line.rstrip('\r\n')
        self.input.emit(line)


class InputThread(qt_core.QThread):

    def __init__(self, parent):
        super().__init__(parent)

    def run(self):
        self._input = Input()
        self.finished.connect(self._input.deleteLater)
        self._input.input.connect(
            self.parent().on_line, qt_core.Qt.QueuedConnection)
        return self.exec_()


class Cmd(cmd.Cmd):
    prompt = f'({e_config_version.SHORT_NAME}) '
    output_sign = '> '
    input_sign = '> '

    def __init__(self):
        super().__init__()

    def _print(self, txt):
        print(self.output_sign + str(txt))

    def do_bye(self, arg):
        "Closing application"
        return True

    def do_EOF(self, line):
        """
        Exit the program. Use  Ctrl-D (Ctrl-Z in Windows) as a shortcut
        """
        return True

    def do_version(self, arg):
        "Returns application version as string"
        self._print('%d.%d.%d' % e_config_version.VERSION)

    def emptyline(self):
        # no commands' shadowing
        pass

    def onecmd(self, line):
        try:
            return super().onecmd(line)
        except ConsoleInputError as ce:
            self._print(ce)
        except gcd.GcdError as gcde:
            self._print(gcde)
        except address.AddressError as ae:
            self._print(ae)
