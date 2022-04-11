from __future__ import annotations

from typing import TYPE_CHECKING

from ...network.query import AbstractJsonQuery
from ...version import Product, tupleToVersionString

if TYPE_CHECKING:
    from typing import Optional


class GitHubNewReleasesApiQuery(AbstractJsonQuery):
    _DEFAULT_URL = Product.VERSION_UPDATE_API_URL
    _DEFAULT_CONTENT_TYPE = "application/vnd.github.v3+json"

    def __init__(self) -> None:
        super().__init__(name_key_tuple=tuple())

    def _processResponse(self, response: Optional[dict, list]) -> None:
        if (
                not self.isSuccess
                and not isinstance(response, list)
                and self.statusCode != 200
        ):
            return

        try:
            version = str(response[0]["tag_name"]).lower().lstrip("v")
            version = tuple(map(int, version.split(".")))
            url = str(response[0]["html_url"]) or Product.VERSION_UPDATE_URL
        except (LookupError, TypeError, ValueError):
            self._logger.warning("Failed to parse GitHub response.")
            return

        if version > Product.VERSION:
            self._logger.info(
                "New version %s available! %s\n%s",
                tupleToVersionString(version),
                url)
            # TODO notify
        else:
            self._logger.debug(
                "Latest version: %s\n%s",
                tupleToVersionString(version),
                url)
