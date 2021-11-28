from __future__ import annotations

import re
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

from ..utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Dict, Final, Tuple


class PasswordStrength:
    _MAP: Final = (
        # Tuple[is_acceptable, name]
        (False, ""),
        (False, QObject().tr("Horrible")),
        (False, QObject().tr("Weak")),
        (False, QObject().tr("Medium")),
        (True,  QObject().tr("Good")),
        (True,  QObject().tr("Strong")),
        (True,  QObject().tr("Paranoiac"))
    )

    def __init__(self, password: str) -> None:
        self._score, self._groups = self._calcScore(password)

        if self._score < 0:
            self._map_index = 0
        elif self._score >= len(self._MAP):
            self._map_index = len(self._MAP) - 1
        else:
            self._map_index = self._score

    @classproperty
    def map(cls) -> Tuple[Tuple[bool, str], ...]:  # noqa
        return cls._MAP

    @classproperty
    def maxNameLength(cls) -> int:  # noqa
        result = 0
        for item in cls._MAP:
            length = len(item[1])
            if length > result:
                result = length
        return result

    @property
    def score(self) -> int:
        return self._score

    @property
    def groups(self) -> Dict[str, bool]:
        return self._groups

    @property
    def isAcceptable(self) -> bool:
        return self._MAP[self._map_index][0]

    @property
    def name(self) -> bool:
        return self._MAP[self._map_index][1]

    @classmethod
    def _calcScore(cls, password: str) -> Tuple[int, Dict[str, bool]]:
        unique_chars = "".join(set(password))
        groups = cls._getGroups(unique_chars)

        if not password:
            return 0, groups

        if len(password) < 8:
            return 1, groups

        if len(unique_chars) < 6:
            return 2, groups

        score = sum(1 for v in groups.values() if v)

        if len(password) > 16:
            score += 1
        if len(unique_chars) > 10:
            score += 1

        return score, groups

    @classmethod
    def _getGroups(cls, unique_chars: str) -> Dict[str, bool]:
        result = dict.fromkeys(
            ("upper", "lower", "numbers", "special"),
            False)

        if unique_chars.lower() != unique_chars:
            result["upper"] = True
        if unique_chars.upper() != unique_chars:
            result["lower"] = True
        if re.search(r"\d", unique_chars):
            result["numbers"] = True
        if re.search(r"\W", unique_chars):
            result["special"] = True

        return result
