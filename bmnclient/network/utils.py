from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote, quote_plus

from PySide6.QtCore import QUrl

from ..utils import NotImplementedInstance

if TYPE_CHECKING:
    from typing import Optional


class NetworkUtils(NotImplementedInstance):
    @staticmethod
    def hostPortToString(host: str, port: int) -> str:
        return "[{:s}]:{:d}".format(host, port)

    @staticmethod
    def quoteUrlQueryItem(source: str) -> Optional[str]:
        try:
            return quote_plus(str(source), errors="strict")
        except UnicodeError:
            return None

    @staticmethod
    def quoteUrlPathItem(item: str):
        try:
            return quote(item, safe="", errors="strict")
        except UnicodeError:
            return None

    @staticmethod
    def isValidUrl(url: str) -> bool:
        if not url:
            return False
        url = QUrl(url, QUrl.StrictMode)
        if (
            not url.isValid()
            # or url.isEmpty()
            or url.isRelative()
            or not url.scheme()
            or not url.host()
        ):
            return False
        return True

    @staticmethod
    def urlJoin(base: str, *args: str) -> Optional[str]:
        if not base:
            return None

        result = base.rstrip("/")
        for item in args:
            item = item.strip("/")
            if item:
                try:
                    item = quote(item, safe="", errors="strict")
                except UnicodeError:
                    return None
                result += "/" + item
        return result
