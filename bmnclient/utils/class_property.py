# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional, Type


class ClassProperty:
    def __init__(self, fget: Any, fset: Any = None) -> None:
        self._fget = fget
        self._fset = fset

    def __get__(self, instance: object, owner: Optional[Type] = None) -> Any:
        if owner is None:
            owner = type(instance)
        return self._fget.__get__(instance, owner)()

    def __set__(self, instance: object, value: Any) -> None:
        if self._fset is None:
            raise AttributeError("can't set attribute")
        owner = type(instance)
        return self._fset.__get__(instance, owner)(value)

    def setter(self, method: Callable) -> ClassProperty:
        if not isinstance(method, classmethod):
            method = classmethod(method)
        self._fset = method
        return self


def classproperty(method: Callable) -> ClassProperty:
    if not isinstance(method, classmethod):
        method = classmethod(method)
    return ClassProperty(method)

