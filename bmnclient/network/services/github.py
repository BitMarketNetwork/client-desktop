from __future__ import annotations

from typing import TYPE_CHECKING

from ...network.query import AbstractJsonQuery
from ...version import Product

if TYPE_CHECKING:
    from typing import Optional


class GitHubNewReleasesApiQuery(AbstractJsonQuery):
    _DEFAULT_URL = "https://api.github.com/repos/BitMarketNetwork/client-desktop/releases"
    _DEFAULT_CONTENT_TYPE = "application/vnd.github.v3+json"

    def __init__(self) -> None:
        super().__init__(name_key_tuple=tuple())

    def _processResponse(self, response: Optional[dict]) -> None:
        Product.VERSION_UPDATE_STRING = response[0]['tag_name'].replace('v', '')
        Product.VERSION_UPDATE_URL = response[0]['html_url']
        self._logger.info(
            "Check update client. Latest version: %s",
            Product.VERSION_UPDATE_STRING)
