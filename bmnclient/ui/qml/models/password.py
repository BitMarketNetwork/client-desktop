from __future__ import annotations

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import QObject
from PySide6.QtCore import Slot as QSlot

from ....crypto.password import PasswordStrength
from . import ValidStatus


class PasswordModel(QObject):
    @QProperty(int, constant=True)
    def maxStrengthNameLength(self) -> int:
        return PasswordStrength.maxNameLength

    @QSlot(str, result="QVariantMap")
    def calcStrength(self, password: str) -> dict[str, ...]:
        s = PasswordStrength(password)
        if not s.score:
            valid_status = ValidStatus.Unset
        elif s.isAcceptable:
            valid_status = ValidStatus.Accept
        else:
            valid_status = ValidStatus.Reject
        return {
            "isAcceptable": s.isAcceptable,
            "name": s.name,
            "status": valid_status.value,
        }
