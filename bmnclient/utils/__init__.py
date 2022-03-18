from __future__ import annotations

from .static_list import StaticList


class NotImplementedInstanceError(Exception):
    pass


class NotImplementedInstance:
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedInstanceError(
            "__init__ not implemented for class '{}'"
            .format(self.__class__.__name__))
