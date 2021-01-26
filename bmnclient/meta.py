from collections import abc
import PySide2.QtCore as qt_core


class classproperty:

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def setdefaultattr(obj, name, value):
    if not hasattr(obj, name):
        setattr(obj, name, value)
    return getattr(obj, name)


class QSeqMeta(type(qt_core.QObject), type(abc.Sequence)):
    pass


class QSeq(qt_core.QObject, abc.Sequence, metaclass=QSeqMeta):
    pass
