# JOK++
from typing import Any, Optional

from ..query import AbstractJsonQuery
from ...logger import Logger
from ...coins.coin import AbstractCoin


class AbstractServerApiQuery(AbstractJsonQuery):
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


class ServerVersionApiQuery(AbstractServerApiQuery):
    _ACTION = "sysinfo"

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Any) -> None:
        if self.statusCode != 200 or data_type is None:
            return

        server_data = {
            "server_url": self._DEFAULT_BASE_URL,
            "server_name": str(value["name"]),
            "server_version_string": str(value["version"][0]),
            "server_version": int(value["version"][1])
        }
        self._logger.info(
            "Server version: %s %s (0x%08x).",
            server_data["server_name"],
            server_data["server_version_string"],
            server_data["server_version"])

        if "coins" in value:
            server_coin_list = value["coins"]
            from ...application import CoreApplication
            for coin in CoreApplication.instance().coinList:
                self._updateCoinRemoteState(
                    coin,
                    server_data,
                    server_coin_list.get(coin.shortName, {}))

    @classmethod
    def _updateCoinRemoteState(
            cls,
            coin: AbstractCoin,
            server_data: dict,
            server_coin_data: dict) -> None:
        server_data = server_data.copy()
        try:
            server_data["version_string"] = str(server_coin_data["version"][0])
            server_data["version"] = int(server_coin_data["version"][1])
        except (LookupError, TypeError, ValueError):
            server_data["version_string"] = "unknown"
            server_data["version"] = -1
        try:
            server_data["height"] = int(server_coin_data["height"])
        except (LookupError, TypeError, ValueError):
            server_data["height"] = -1
        try:
            server_data["status"] = int(server_coin_data["status"])
        except (LookupError, TypeError, ValueError):
            server_data["status"] = -1

        coin.serverData = server_data


class CoinsInfoApiQuery(AbstractServerApiQuery):
    _ACTION = "coins"

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Any) -> None:
        if self.statusCode != 200 or data_type is None:
            return