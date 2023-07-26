from __future__ import annotations

from typing import Optional, Tuple, Union

from .instance import NotImplementedInstance

ClassStringKeyTuple = Tuple[Optional[str], Optional[Union[str, int]]]


class StringUtils(NotImplementedInstance):
    @classmethod
    def stripLeft(cls, source: str, symbol_list: str) -> tuple[int, str]:
        offset = 0
        for c in source:
            if c not in symbol_list:
                break
            offset += 1
        if offset:
            return offset, source[offset:]
        return offset, source

    @classmethod
    def stripRight(cls, source: str, symbol_list: str) -> tuple[int, str]:
        offset = 0
        for c in reversed(source):
            if c not in symbol_list:
                break
            offset += 1
        if offset:
            return offset, source[:-offset]
        return offset, source

    @classmethod
    def toSnakeCase(cls, source: str, *, symbol: str = "_") -> str:
        symbol = symbol[0]
        l_offset, source = cls.stripLeft(source, symbol)
        r_offset, source = cls.stripRight(source, symbol)

        # remove symbol if next char not lower
        source = [
            c
            for i, c in enumerate(source)
            if c != symbol or (c == symbol and source[i + 1].islower())
        ]

        # convert upper to (symbol + lower)
        source = [symbol + c.lower() if c.isupper() else c for c in source]

        if source and source[0].startswith(symbol):
            source[0] = source[0][1:]

        return symbol * l_offset + "".join(source) + symbol * r_offset

    @classmethod
    def toCamelCase(
        cls, source: str, *, symbol: str = "_", first_lower: bool = True
    ) -> str:
        symbol = symbol[0]
        l_offset, source = cls.stripLeft(source, symbol)
        r_offset, source = cls.stripRight(source, symbol)

        source = source.split(symbol)
        source = [c[0:1].upper() + c[1:].lower() for c in source]

        if first_lower and source:
            source[0] = source[0].lower()

        return symbol * l_offset + "".join(source) + symbol * r_offset

    @staticmethod
    def classString(
        cls_: type(object),
        *key_list: ClassStringKeyTuple,
        parent: object | type(object) | None = None,
    ) -> str:
        result = []
        for name, value in key_list:
            if name:
                result.append(str(name) + "=" + str(value))
            else:
                result.append(str(value))

        class_name = cls_.__name__.lstrip("_")  # remove private marker
        if class_name.startswith("Abstract"):
            class_name = class_name[8:]

        if result:
            class_name += "[" + ":".join(result) + "]"

        if parent is not None:
            class_name = str(parent) + "." + class_name

        return class_name
