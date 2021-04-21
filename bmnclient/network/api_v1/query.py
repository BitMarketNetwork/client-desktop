# JOK++
from typing import Any, Optional

from ..query import AbstractJsonQuery
from ...coins.coin import AbstractCoin
from ...logger import Logger
from ...utils.serialize import ParseError, parseItemKey


class AbstractServerApiQuery(AbstractJsonQuery):
    _DEFAULT_CONTENT_TYPE = "application/vnd.api+json"
    _DEFAULT_BASE_URL = "https://d1.bitmarket.network:30110/v1/"  # TODO dynamic
    _ACTION = ""

    @property
    def url(self) -> str:
        return super().url + self._ACTION

    def __processErrorList(self, error_list: list) -> None:
        if not error_list:
            raise ParseError("empty error list")
        for error in error_list:
            self._processError(
                parseItemKey(error, "code", int),
                parseItemKey(error, "detail", str))

    def __processData(self, data: dict) -> None:
        data_id = parseItemKey(data, "id", str)
        data_type = parseItemKey(data, "type", str)
        data_attributes = parseItemKey(data, "attributes", dict, {})
        self._processData(data_id, data_type, data_attributes)

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
                raise ParseError("empty response")

            meta = parseItemKey(response, "meta", dict, {})
            if parseItemKey(meta, "timeframe", int, 0) > 1e9:
                self._logger.warning(
                    "Server response has taken more than 1 second.")
        except ParseError as e:
            self._logger.error("Invalid server response: %s.", str(e))

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


class ServerInfoApiQuery(AbstractServerApiQuery):
    _ACTION = "sysinfo"

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Any) -> None:
        if self.statusCode != 200 or data_type is None:
            return

        server_version = parseItemKey(value, "version", list)
        server_data = {
            "server_url": self._DEFAULT_BASE_URL,
            "server_name": parseItemKey(value, "name", str),
            "server_version_string": parseItemKey(server_version, 0, str),
            "server_version": parseItemKey(server_version, 1, int)
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

    def _updateCoinRemoteState(
            self,
            coin: AbstractCoin,
            server_data: dict,
            server_coin_data: dict) -> None:
        try:
            coin_version = parseItemKey(server_coin_data, "version", list)
            coin.serverData = {
                **server_data,
                "version_string": parseItemKey(coin_version, 0, str),
                "version": parseItemKey(coin_version, 1, int),
                "height": parseItemKey(server_coin_data, "height", int),
                "status": parseItemKey(server_coin_data, "status", int),
            }
        except ParseError as e:
            coin.serverData = server_data
            self._logger.error(
                "Failed to parse coin info \"{}\": {}"
                .format(coin.fullName, str(e)))


class CoinsInfoApiQuery(AbstractServerApiQuery):
    _ACTION = "coins"

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Any) -> None:
        if self.statusCode != 200 or data_type is None:
            return

        from ...application import CoreApplication
        for coin in CoreApplication.instance().coinList:
            coin_info = value.get(coin.shortName)
            if not coin_info:
                self._logger.warning("TODO")
                continue

            state_hash = coin.stateHash
            try:
                offset = parseItemKey(
                    coin_info,
                    "offset",
                    str)
                unverified_offset = parseItemKey(
                    coin_info,
                    "unverified_offset",
                    str)
                unverified_hash = parseItemKey(
                    coin_info,
                    "unverified_hash",
                    str)
                height = parseItemKey(
                    coin_info,
                    "height",
                    int)
                verified_height = parseItemKey(
                    coin_info,
                    "verified_height",
                    int)
                status = parseItemKey(
                    coin_info,
                    "status",
                    int)
            except ParseError as e:
                self._logger.error(
                    "Failed to parse coin \"{}\": {}"
                    .format(coin.fullName, str(e)))
                continue

            # TODO legacy order
            coin.status = status
            coin.unverifiedHash = unverified_hash
            coin.unverifiedOffset = unverified_offset
            coin.offset = offset
            coin.verifiedHeight = verified_height
            coin.height = height
