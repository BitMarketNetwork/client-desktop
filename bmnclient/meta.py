
import sys
import logging
import functools
from collections import abc
import PySide2.QtCore as qt_core

log = logging.getLogger()

_plat = sys.platform.lower()
IS_WINDOWS = 'win32' in _plat or 'win64' in _plat
IS_OSX = 'darwin' in _plat
IS_FREEBSD = 'freebsd' in _plat
IS_NETBSD = 'netbsd' in _plat
IS_BSD = IS_FREEBSD or IS_NETBSD
IS_LINUX = not(IS_WINDOWS or IS_OSX or IS_BSD)


def lazy_property(f):
    return property(functools.lru_cache()(f))


def trace(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        import pdb
        pdb.set_trace()
        log.warning(f"{func} result: {result}")
        return result
    return wrapper


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
