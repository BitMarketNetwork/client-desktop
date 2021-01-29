# JOK++
import re


class PasswordStrength:
    def __init__(self, password: str) -> None:
        self._password = password
        self._unique = "".join(set(password))

    def calc(self) -> int:
        if not self._password or len(self._password) < 8:
            return 1
        if len(self._unique) < 6:
            return 2

        result = len([v for v in self._getCharGroups().values() if v])

        if len(self._password) > 16:
            result += 1
        if len(self._unique) > 10:
            result += 1

        return result

    def _getCharGroups(self) -> dict:
        result = dict.fromkeys(
            ["upper", "lower", "numbers", "special"],
            0)

        if self._unique.lower() != self._unique:
            result["upper"] = True
        if self._unique.upper() != self._unique:
            result["lower"] = True
        if re.search(r"\d", self._unique):
            result["numbers"] = True
        if re.search(r"\W", self._unique):
            result["special"] = True

        return result
