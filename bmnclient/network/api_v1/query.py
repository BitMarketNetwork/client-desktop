# JOK++
from typing import Any, Optional

from ..query import AbstractJsonQuery
from ...logger import Logger
from ...coins.coin import AbstractCoin


class ServerApiQuery(AbstractJsonQuery):
    _DEFAULT_CONTENT_TYPE = "application/vnd.api+json"
    _DEFAULT_BASE_URL = "https://d1.bitmarket.network:30110/v1/"  # TODO dynamic
    _ACTION = ""

    @property
    def url(self) -> str:
        return super().url + self._ACTION

    def __processErrorList(self, error_list: list) -> None:
        if not error_list:
            raise LookupError("empty error list")
        for error in error_list:
            self._processError(int(error["code"]), error["detail"])

    def __processData(self, data: dict) -> None:
        data_id = str(data["id"])
        data_type = str(data["type"])
        data_attributes = data.get("attributes", None)
        self._processData(data_id,  data_type, data_attributes)

    def _processResponse(self, response: Optional[dict]) -> None:
        try:
            if response is None:
                self._logger.debug("Empty response.")
                self._processData(None, None, None)
                return

            # The members data and errors MUST NOT coexist in the same
            # document.
            if "errors" in response:
                self.__processErrorList(response["errors"])
            elif "data" in response:
                self.__processData(response["data"])
            else:
                raise LookupError("empty response")
        except KeyError as e:
            self._logger.error(
                "Invalid server response: key %s not found.",
                str(e).replace("'", "\""))
        except (LookupError, TypeError, ValueError) as e:
            self._logger.error("Invalid server response: %s.", str(e))

        meta = response.get("meta", {})
        if "timeframe" in meta:
            if int(meta["timeframe"]) > 1e9:
                self._logger.warning(
                    "Server answer has taken more than 1s.")

    def _processError(self, error: int, message: str) -> None:
        self._logger.error(
            "Server error: %s",
            Logger.errorToString(error, message))

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Any) -> None:
        raise NotImplementedError


class CheckServerVersionApiQuery(ServerApiQuery):
    _ACTION = "sysinfo"

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Any) -> None:
        if self.statusCode != 200 or data_type != self._ACTION:
            return

        server_name = str(value["name"])
        server_version_string = str(value["version"][0])
        server_version = int(value["version"][1])
        self._logger.info(
            "Server version: %s %s (0x%08x).",
            server_name,
            server_version_string,
            server_version)

        if "coins" in value:
            server_coin_list = value["coins"]
            from ...application import CoreApplication
            for coin in CoreApplication.instance().coinList:
                self._updateCoinRemoteState(
                    coin,
                    server_coin_list.get(coin.shortName, {}))

    def _updateCoinRemoteState(
            self,
            coin: AbstractCoin,
            data: dict) -> None:
        remote_data = {}
        try:
            remote_data["version_string"] = str(data["version"][0])
            remote_data["version"] = int(data["version"][1])
        except (LookupError, TypeError, ValueError):
            remote_data["version_string"] = "unknown"
            remote_data["version"] = -1
        try:
            remote_data["height"] = int(data["height"])
        except (LookupError, TypeError, ValueError):
            remote_data["height"] = -1
        try:
            remote_data["status"] = int(data["status"])
        except (LookupError, TypeError, ValueError):
            remote_data["status"] = -1

        # TODO
        coin._remote = remote_data
        coin.model.remoteState.refresh()
        #    gui_api.uiManager.serverVersion = versions[1]
