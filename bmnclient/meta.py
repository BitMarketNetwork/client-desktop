import logging
import functools
import typing
from collections import abc
import PySide2.QtCore as qt_core

log = logging.getLogger()


def lazy_property(f):
    return property(functools.lru_cache()(f))


class classproperty:

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def setdefaultattr(obj, name, value):
    if not hasattr(obj, name):
        setattr(obj, name, value)
    return getattr(obj, name)


def debug(func):
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        log.warning(
            f"META:Calling {func.__name__}({', '.join( [repr(a) for a in args]  + kwargs_repr)}")
        value = func(*args, **kwargs)
        log.warning(f"META:{func.__name__!r} returned {value!r}")
        return value
    return wrapper_debug


class QSeqMeta(type(qt_core.QObject), type(abc.Sequence)):
    pass


class QSeq(qt_core.QObject, abc.Sequence, metaclass=QSeqMeta):
    pass
