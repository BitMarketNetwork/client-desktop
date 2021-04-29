# JOK+++
from __future__ import annotations

from enum import auto, Flag
from typing import TYPE_CHECKING

from ...coins.tx import AbstractTx

if TYPE_CHECKING:
    from typing import Any, Callable, Final, List, Optional, Type, Union
    from ...coins.address import AbstractAddress


class ParseError(LookupError):
    pass


class AbstractParser:
    class ParseFlag(Flag):
        pass

    def __init__(
            self,
            flags: Optional[AbstractParser.ParseFlag] = None) -> None:
        self._flags = flags

    @classmethod
    def parseKey(
            cls,
            item: Union[dict, list],
            key_name: Union[str, int],
            value_type: Type,
            default_value: Any = None,
            *,
            allow_none=False,
            allow_convert=False) -> Any:
        try:
            value = item[key_name]

            if value is None:
                if allow_none:
                    return None
                if allow_convert:
                    return 0
                raise ValueError

            if isinstance(value, value_type):
                return value
            if allow_convert:
                return value_type(value)

            raise TypeError
        except (KeyError, IndexError):
            if default_value is not None:
                return default_value
            raise ParseError(
                "key \"{}\" not found".format(str(key_name)))
        except (TypeError, ValueError):
            raise ParseError(
                "invalid value for key \"{}\"".format(str(key_name)))


class ResponseErrorParser(AbstractParser):
    def parse(
            self,
            response: dict,
            callback: Callable[[int, str], None]) -> None:
        error_list = self.parseKey(response, "errors", list)
        if not error_list:
            raise ParseError("empty error list")
        for error in error_list:
            callback(
                self.parseKey(error, "code", int, allow_convert=True),
                self.parseKey(error, "detail", str))


class ResponseDataParser(AbstractParser):
    def parse(
            self,
            response: dict,
            callback: Callable[[str, str, dict], None]) -> None:
        data = self.parseKey(response, "data", dict)
        data_id = self.parseKey(data, "id", str)
        data_type = self.parseKey(data, "type", str)
        data_attributes = self.parseKey(data, "attributes", dict, {})
        callback(data_id, data_type, data_attributes)


class ResponseMetaParser(AbstractParser):
    SLOW_TIMEFRAME: Final = 1e9

    def __init__(self) -> None:
        super().__init__()
        self._timeframe = 0

    @property
    def timeframe(self) -> int:
        return self._timeframe

    @property
    def timeframeSeconds(self) -> int:
        return int(self._timeframe // 1e9)

    def parse(self, response: dict) -> None:
        meta = self.parseKey(response, "meta", dict, {})
        self._timeframe = self.parseKey(meta, "timeframe", int, 0)


class SysinfoParser(AbstractParser):
    def __init__(self) -> None:
        super().__init__()
        self._server_data = {}
        self._server_coin_list = {}

    @property
    def serverData(self) -> dict:
        return self._server_data

    @property
    def serverCoinList(self) -> dict:
        return self._server_coin_list

    def parse(self, value: dict, server_url: str) -> None:
        server_version = self.parseKey(value, "version", list)
        self._server_data = {
            "server_url": server_url,
            "server_name": self.parseKey(value, "name", str),
            "server_version_string": self.parseKey(server_version, 0, str),
            "server_version": self.parseKey(server_version, 1, int)
        }

        self._server_coin_list.clear()
        server_coin_list = self.parseKey(value, "coins", dict)
        for (coin_name, coin_value) in server_coin_list.items():
            try:
                self._server_coin_list[coin_name] = self._parseCoin(coin_value)
            except ParseError as e:
                raise ParseError(
                    "failed to parse coin \"{}\": {}"
                    .format(coin_name, str(e)))

    def _parseCoin(self, value: dict) -> dict:
        coin_version = self.parseKey(value, "version", list)
        return {
            "version_string": self.parseKey(coin_version, 0, str),
            "version": self.parseKey(coin_version, 1, int),
            "height": self.parseKey(value, "height", int),
            "status": self.parseKey(value, "status", int),
        }


class CoinsInfoParser(AbstractParser):
    def __init__(self) -> None:
        super().__init__()
        self._offset = ""
        self._unverified_offset = ""
        self._unverified_hash = ""
        self._height = -1
        self._verified_height = -1
        self._status = -1

    @property
    def offset(self) -> str:
        return self._offset

    @property
    def unverifiedOffset(self) -> str:
        return self._unverified_offset

    @property
    def unverifiedHash(self) -> str:
        return self._unverified_hash

    @property
    def height(self) -> int:
        return self._height

    @property
    def verifiedHeight(self) -> int:
        return self._verified_height

    @property
    def status(self) -> int:
        return self._status

    def parse(self, value: dict, coin_name: str) -> bool:
        coin_info = self.parseKey(value, coin_name, dict, {})
        if not coin_info:
            return False

        try:
            self._offset = self.parseKey(
                coin_info,
                "offset",
                str)
            self._unverified_offset = self.parseKey(
                coin_info,
                "unverified_offset",
                str)
            self._unverified_hash = self.parseKey(
                coin_info,
                "unverified_hash",
                str)
            self._height = self.parseKey(
                coin_info,
                "height",
                int)
            self._verified_height = self.parseKey(
                coin_info,
                "verified_height",
                int)
            self._status = self.parseKey(
                coin_info,
                "status",
                int)
        except ParseError as e:
            raise ParseError(
                "failed to parse coin \"{}\": {}"
                .format(coin_name, str(e)))

        return True


class TxParser(AbstractParser):
    class ParseFlag(AbstractParser.ParseFlag):
        NONE: Final = auto()
        MEMPOOL: Final = auto()

    def __init__(self, flags=ParseFlag.NONE) -> None:
        super().__init__(flags=flags)

    def parseList(
            self,
            response: dict,
            address: AbstractAddress) -> Optional[List[AbstractTx]]:
        result = []
        for (name, value) in response.items():
            tx = self.parse(name, value, address)
            if tx is None:
                return None
            result.append(tx)
        return result

    def parse(
            self,
            name: str,
            response: dict,
            address: AbstractAddress) -> Optional[AbstractTx]:
        try:
            if self._flags & self.ParseFlag.MEMPOOL:
                self.parseKey(response, "height", type(None), allow_none=True)
                height = -1
            else:
                height = self.parseKey(response, "height", int)

            data = {
                "name": name,
                "height": height,
                "time": self.parseKey(response, "time", int),
                "amount": self.parseKey(response, "amount", int),
                "fee": self.parseKey(response, "fee", int),
                "coinbase": self.parseKey(response, "coinbase", int) != 0,

                "input_list": [
                    self._parseIo(v) for v in self.parseKey(
                        response,
                        "input",
                        list)
                ],
                "output_list": [
                    self._parseIo(v) for v in self.parseKey(
                        response,
                        "output",
                        list)
                ]
            }
        except ParseError as e:
            raise ParseError(
                "failed to parse transaction \"{}\": {}"
                .format(name, str(e)))

        return AbstractTx.deserialize(address, **data)

    @classmethod
    def _parseIo(cls, item: dict) -> dict:
        return {
            "output_type": cls.parseKey(item, "output_type", str),
            "address_type": cls.parseKey(item, "type", str, allow_none=True),
            "address_name": cls.parseKey(item, "address", str, allow_none=True),
            "amount": cls.parseKey(item, "amount", int)
        }
