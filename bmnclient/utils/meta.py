# JOK++
from __future__ import annotations

from typing import Any


class ClassProperty:
    def __init__(self, fget=None, fset=None) -> None:
        self._fget = fget
        self._fset = fset

    def __get__(self, instance, owner=None) -> Any:
        if owner is None:
            owner = type(instance)
        return self._fget.__get__(instance, owner)()

    def __set__(self, instance, value) -> None:
        if not self._fset:
            raise AttributeError("can't set attribute")
        owner = type(instance)
        return self._fset.__get__(instance, owner)(value)

    def setter(self, func) -> ClassProperty:
        if not isinstance(func, classmethod):
            func = classmethod(func)
        self._fset = func
        return self


def classproperty(func) -> ClassProperty:
    if not isinstance(func, classmethod):
        func = classmethod(func)
    return ClassProperty(func)
