from __future__ import annotations


class NotImplementedInstanceError(Exception):
    pass


class NotImplementedInstance:
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedInstanceError(
            "__init__ not implemented for class '{}'"
                .format(self.__class__.__name__))
