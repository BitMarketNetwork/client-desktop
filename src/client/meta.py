
import sys
import logging

log = logging.getLogger()

_plat = sys.platform.lower()
IS_WINDOWS = 'win32' in _plat or 'win64' in _plat
IS_OSX = 'darwin' in _plat
IS_FREEBSD = 'freebsd' in _plat
IS_NETBSD = 'netbsd' in _plat
IS_DRAGONFLYBSD = 'dragonfly' in _plat
IS_BSD = IS_FREEBSD or IS_NETBSD or IS_DRAGONFLYBSD
IS_LINUX = not(IS_WINDOWS or IS_OSX or IS_BSD)

def trace(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        log.debug(f"{func} result: {result}")
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
