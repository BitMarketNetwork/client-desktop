# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote, quote_plus

from PySide2.QtCore import QUrl

from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional


class NetworkUtils(NotImplementedInstance):
    @staticmethod
    def hostPortToString(host: str, port: int) -> str:
        return "[{:s}]:{:d}".format(host, port)

    @staticmethod
    def encodeUrlString(source: str) -> Optional[str]:
        try:
            return quote_plus(
                str(source),
                encoding="utf-8",
                errors="strict")
        except UnicodeError:
            return None

    @staticmethod
    def isValidUrl(url: str) -> bool:
        if url and QUrl(url, QUrl.StrictMode).isValid():
            return True
        return False

    @staticmethod
    def urlJoin(base: str, *args: str) -> Optional[str]:
        if not base:
            return None

        result = base.rstrip("/")
        for item in args:
            item = item.strip("/")
            if item:
                try:
                    item = quote(
                        item,
                        safe="",
                        encoding="utf-8",
                        errors="strict")
                except UnicodeError:
                    return None
                result += "/" + item
        return result
