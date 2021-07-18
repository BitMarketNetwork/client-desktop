from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Generator, Iterable


class NotImplementedInstanceError(Exception):
    pass


class NotImplementedInstance:
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedInstanceError(
            "__init__ not implemented for class '{}'"
            .format(self.__class__.__name__))


class Utils(NotImplementedInstance):
    @staticmethod
    def filterNotNone(iterable: Iterable) -> Generator[Any, None, None]:
        for v in iterable:
            if v is not None:
                yield v
