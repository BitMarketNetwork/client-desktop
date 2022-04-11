from __future__ import annotations

from typing import TYPE_CHECKING
import json

from ...network.query import AbstractJsonQuery, AbstractQuery
from ...version import Product

if TYPE_CHECKING:
    from typing import Dict, Optional, Union


class GithubNewReleasesApiQuery(AbstractJsonQuery):
    _FULL_NAME = "GithubApi"
    _DEFAULT_URL = "https://api.github.com/repos/BitMarketNetwork/client-desktop/releases"
    _DEFAULT_CONTENT_TYPE = "application/vnd.github.v3+json"

    def __init__(self) -> None:
        AbstractJsonQuery.__init__(self, name_key_tuple=())
        self._response_data = None

    def _jsonResponseContent(self, data: bytes) -> Optional[dict]:
        value = data
        if value:
            try:
                value = json.loads(value)
                self._logger.debug("JSON Response: %s", value)
                return value
            except UnicodeError as e:
                self._logger.error(
                    "Failed to encode JSON response: %s",
                    str(e))
            except json.JSONDecodeError as e:
                self._logger.error(
                    "Failed to encode JSON response: %s",
                    str(e))

        return None

    def _onResponseData(self, data: bytes) -> bool:
        self._response_data = bytes(data)
        json_data = self._jsonResponseContent(self._response_data)
        if json_data is None:
            return False
        Product.VERSION_UPDATE_STRING = json_data[0]['tag_name'].replace('v','')
        Product.VERSION_UPDATE_URL = json_data[0]['html_url']
        self._logger.info(
                "Check update client. Latest version: %s ", Product.VERSION_UPDATE_STRING)
        return True

    def _processResponse(self, response: Optional[dict]) -> None:
        return
