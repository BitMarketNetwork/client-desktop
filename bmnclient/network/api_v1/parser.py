# JOK4
from __future__ import annotations

import itertools
from enum import auto, Flag
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Final, List, Optional, Type, Union
    from ...coins.abstract.coin import AbstractCoin


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
            allow_none: bool = False,
            allow_convert: bool = False) -> Any:
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


class ResponseParser(AbstractParser):
    def __call__(
            self,
            response: dict,
            callback: Callable[[str, str, dict], None],
            error_callback: Callable[[int, str], None]) -> None:
        # The members data and errors MUST NOT coexist in the same
        # document.
        if "errors" in response:
            error_list = self.parseKey(response, "errors", list)
            if not error_list:
                raise ParseError("empty error list")
            for error in error_list:
                error_callback(
                    self.parseKey(error, "code", int, allow_convert=True),
                    self.parseKey(error, "detail", str))
        elif "data" in response:
            data = self.parseKey(response, "data", dict)
            data_id = self.parseKey(data, "id", str)
            data_type = self.parseKey(data, "type", str)
            data_attributes = self.parseKey(data, "attributes", dict, {})
            callback(data_id, data_type, data_attributes)
        else:
            raise ParseError("empty response")


class ResponseMetaParser(AbstractParser):
    SLOW_TIMEFRAME: Final = 1e9

    def __init__(self) -> None:
        super().__init__()
        self._timeframe = 0

    @property
    def isSlowResponse(self) -> bool:
        return self._timeframe > self.SLOW_TIMEFRAME

    @property
    def timeframe(self) -> int:
        return self._timeframe

    @property
    def timeframeSeconds(self) -> int:
        return int(self._timeframe // 1e9)

    def __call__(self, response: dict) -> None:
        meta = self.parseKey(response, "meta", dict, {})
        self._timeframe = self.parseKey(meta, "timeframe", int, 0)


class TxParser(AbstractParser):
    class ParseFlag(AbstractParser.ParseFlag):
        NONE: Final = auto()
        MEMPOOL: Final = auto()

    def __init__(self, flags: ParseFlag = ParseFlag.NONE) -> None:
        super().__init__(flags)

    def __call__(
            self,
            name: str,
            value: dict) -> Dict[str, Any]:
        if self._flags & self.ParseFlag.MEMPOOL:
            # TODO fix server
            # self.parseKey(value, "height", type(None), allow_none=True)
            height = -1
        else:
            height = self.parseKey(value, "height", int)

        return {
            "name": name,
            "height": height,
            "time": self.parseKey(value, "time", int),
            "amount": self.parseKey(value, "amount", int),
            "fee_amount": self.parseKey(value, "fee", int),
            "coinbase": self.parseKey(value, "coinbase", int) != 0,

            "input_list": [
                self._parseIo(v) for v in self.parseKey(
                    value,
                    "input",
                    list)
            ],
            "output_list": [
                self._parseIo(v) for v in self.parseKey(
                    value,
                    "output",
                    list)
            ]
        }

    def _parseIo(self, item: dict) -> dict:
        self.parseKey(
            item,
            "type",
            str,
            allow_none=True)

        return {
            "output_type": self.parseKey(
                item,
                "output_type",
                str),
            "address_name": self.parseKey(
                item,
                "address",
                str,
                allow_none=True),
            "amount": self.parseKey(
                item,
                "amount",
                int)
        }


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

    def __call__(self, value: dict, server_url: str) -> None:
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

    def __call__(self, value: dict, coin_name: str) -> bool:
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


class AddressInfoParser(AbstractParser):
    def __init__(self) -> None:
        super().__init__()
        self._type = ""
        self._name = ""
        self._tx_count = 0
        self._amount = 0

    @property
    def type(self) -> str:
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def txCount(self) -> int:
        return self._tx_count

    @property
    def amount(self) -> int:
        return self._amount

    def __call__(self, value: dict) -> None:
        self._type = self.parseKey(value, "type", str)
        self._name = self.parseKey(value, "address", str)
        self._tx_count = self.parseKey(value, "number_of_transactions", int)
        self._amount = self.parseKey(value, "balance", int)


class AddressTxParser(AbstractParser):
    def __init__(self, address: AbstractCoin.Address) -> None:
        super().__init__()
        self._address = address
        self._address_type = ""
        self._address_name = ""
        self._first_offset = ""
        self._last_offset: Optional[str] = None
        self._tx_list: List[AbstractCoin.Tx] = []

    @property
    def addressType(self) -> str:
        return self._address_type

    @property
    def addressName(self) -> str:
        return self._address_name

    @property
    def firstOffset(self) -> str:
        return self._first_offset

    @property
    def lastOffset(self) -> Optional[str]:
        return self._last_offset

    @property
    def txList(self) -> List[AbstractCoin.Tx]:
        return self._tx_list

    def __call__(self, value: dict) -> None:
        self._address_type = self.parseKey(
            value,
            "type",
            str)
        self._address_name = self.parseKey(
            value,
            "address",
            str)
        self._first_offset = self.parseKey(
            value,
            "first_offset",
            str)
        self._last_offset = self.parseKey(
            value,
            "last_offset",
            str,
            allow_none=True)
        self._parseTxList(value)

    def _parseTxList(self, value: dict):
        tx_value_list = self.parseKey(value, "tx_list", dict)
        tx_parser = TxParser()
        for (tx_name, tx_value) in tx_value_list.items():
            try:
                tx = self._address.coin.Tx.deserialize(
                    self._address,
                    **tx_parser(tx_name, tx_value))
                self._tx_list.append(tx)
            except ParseError as e:
                raise ParseError(
                    "failed to parse transaction \"{}\": {}"
                    .format(tx_name, str(e)))


class AddressUtxoParser(AddressTxParser):
    def __init__(self, address: AbstractCoin.Address) -> None:
        super().__init__(address)
        self._tx_list: List[AbstractCoin.Tx.Utxo] = []

    @property
    def txList(self) -> List[AbstractCoin.Tx.Utxo]:
        return self._tx_list

    def _parseTxList(self, value: dict):
        tx_value_list = self.parseKey(value, "tx_list", list)
        for (tx_index, tx_value) in enumerate(tx_value_list):
            try:
                height = self.parseKey(tx_value, "height", int, allow_none=True)
                if height is None:  # TODO mempool (no server support)
                    height = -1
                data = {
                    "name": self.parseKey(tx_value, "tx", str),
                    "height": height,
                    "index": self.parseKey(tx_value, "index", int),
                    "amount": self.parseKey(tx_value, "amount", int)
                }
                if data["amount"] > 0:
                    utxo = self._address.coin.Tx.Utxo.deserialize(
                        self._address,
                        **data)
                    self._tx_list.append(utxo)
            except ParseError as e:
                raise ParseError(
                    "failed to parse UTXO \"{}\": {}"
                    .format(tx_index, str(e)))


class CoinMempoolParser(AbstractParser):
    def __init__(
            self,
            coin: AbstractCoin) -> None:
        super().__init__()
        self._coin = coin
        self._hash = ""
        self._tx_list: List[AbstractCoin.Tx] = []

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def txList(self) -> List[AbstractCoin.Tx]:
        return self._tx_list

    def __call__(self, value: dict) -> None:
        self._hash = self.parseKey(value, "hash", str)

        tx_value_list = self.parseKey(value, "tx_list", dict)
        tx_parser = TxParser(TxParser.ParseFlag.MEMPOOL)
        for (tx_name, tx_value) in tx_value_list.items():
            try:
                self._processTxData(tx_parser(tx_name, tx_value))
            except ParseError as e:
                raise ParseError(
                    "failed to parse unconfirmed transaction \"{}\": {}"
                    .format(tx_name, str(e)))

    def _processTxData(self, tx_data: Dict[str, Any]) -> None:
        tx_io_list = itertools.chain(
            tx_data["input_list"],
            tx_data["output_list"])

        for tx_io in tx_io_list:
            address_name = tx_io["address_name"]
            if address_name is not None:
                address = self._coin.findAddressByName(address_name)
                if address is not None:
                    tx = address.coin.Tx.deserialize(address, **tx_data)
                    self._tx_list.append(tx)


class BroadcastTxParser(AbstractParser):
    def __init__(self) -> None:
        super().__init__()
        self._txName = ""

    @property
    def txName(self) -> str:
        return self._txName

    def __call__(self, value: dict) -> None:
        self._txName = self.parseKey(value, "tx", str)

