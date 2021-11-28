from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import \
    Property as QProperty, \
    QObject, \
    Slot as QSlot

from . import ValidStatus
from ....crypto.password import PasswordStrength

if TYPE_CHECKING:
    from typing import Any, Dict


class PasswordModel(QObject):
    @QProperty(int, constant=True)
    def maxStrengthNameLength(self) -> int:
        return PasswordStrength.maxNameLength

    @QSlot(str, result="QVariantMap")
    def calcStrength(self, password: str) -> Dict[str, Any]:
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
            "status": valid_status.value
        }
