from __future__ import annotations

from enum import Enum


class Column:
    __slots__ = ("_name", "_identifier", "_definition", "_full_definition")

    def __init__(self, name: str, definition: str) -> None:
        self._name = name
        self._identifier = f"\"{self._name}\""
        self._definition = definition
        self._full_definition = f"{self._identifier} {self._definition}"

    def __str__(self) -> str:
        return self._full_definition

    @property
    def name(self) -> str:
        return self._name

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def definition(self) -> str:
        return self._definition


class ColumnEnum(Column, Enum):
    def __init__(
            self,
            name: str = "row_id",
            definition: str = "INTEGER PRIMARY KEY") -> None:
        super().__init__(name, definition)
