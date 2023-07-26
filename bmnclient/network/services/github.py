from __future__ import annotations

from typing import TYPE_CHECKING

from ...network.query import AbstractJsonQuery
from ...version import Product, tupleToVersionString

if TYPE_CHECKING:
    from typing import Optional

    from ...application import CoreApplication


class GitHubNewReleasesApiQuery(AbstractJsonQuery):
    _DEFAULT_URL = Product.VERSION_UPDATE_API_URL
    _DEFAULT_CONTENT_TYPE = "application/vnd.github.v3+json"

    def __init__(self, application: CoreApplication) -> None:
        super().__init__(name_key_tuple=tuple())
        self._application = application

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
            # TODO parse change log from current_version <-> latest version
        except (LookupError, TypeError, ValueError):
            self._logger.warning("Failed to parse GitHub response.")
            return

        if version > Product.VERSION:
            self._logger.info(
                "New version %s available! %s",
                tupleToVersionString(version),
                url,
            )

            # FIXME
            # class UpdateInfo + CoreApplication.updateInfo property
            if context := getattr(self._application, "qmlContext", None):
                context.update.set(version, url)
        else:
            self._logger.debug(
                "Latest version: %s\n%s", tupleToVersionString(version), url
            )
