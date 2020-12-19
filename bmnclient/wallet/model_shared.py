
import enum
import PySide2.QtCore as qt_core # pylint: disable=import-error


def ba(s): return qt_core.QByteArray(s)


class IntEnum(enum.IntEnum):
    def _generate_next_value_(name, start, count, last_values):  # pylint: disable=no-self-argument
        return count + qt_core.Qt.UserRole + 1001
