from __future__ import annotations

from typing import TYPE_CHECKING

from ..logger import Logger
from .utils import NetworkUtils

if TYPE_CHECKING:
    from typing import List, Optional


class ServerList:
    def __init__(self, allow_insecure: bool = False) -> None:
        self._logger = Logger.classLogger(self.__class__)
        self._url_list: List[str] = []
        self._allow_insecure = allow_insecure

    def appendServer(self, url: str) -> bool:
        url = url.strip()
        if not NetworkUtils.isValidUrl(url):
            self._logger.debug("Invalid server URL '%s'.", url)
            return False
        if url in self._url_list:
            self._logger.debug("Server URL '%s' is already on the list.", url)
            return False
        self._url_list.append(url)
        self._logger.debug("Available server URL: %s", url)
        return True

    @property
    def allowInsecure(self) -> bool:
        return self._allow_insecure

    @property
    def currentServerUrl(self) -> Optional[str]:
        if self._url_list:
            return self._url_list[0]
        return None
