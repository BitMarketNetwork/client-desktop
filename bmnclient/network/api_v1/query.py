# JOK4
from __future__ import annotations

import itertools
from enum import auto, Enum
from typing import TYPE_CHECKING

from .parser import \
    AddressInfoParser, \
    AddressTxParser, \
    AddressUtxoParser, \
    BroadcastTxParser, \
    CoinMempoolParser, \
    CoinsInfoParser, \
    ParseError, \
    ResponseMetaParser, \
    ResponseParser, \
    SysinfoParser
from ..query import AbstractJsonQuery
from ..utils import urlJoin
from ...coins.hd import HdAddressIterator
from ...logger import Logger

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Final, List, Optional, Tuple, Union
    from ...coins.abstract.coin import AbstractCoin
    from ...coins.list import CoinList
    from ...utils.serialize import DeserializedData
    from ...wallet.mtx_impl import Mtx


class AbstractApiQuery(AbstractJsonQuery):
    _DEFAULT_CONTENT_TYPE = "application/vnd.api+json"
    _DEFAULT_BASE_URL = "https://d1.bitmarket.network:30110/"  # TODO dynamic
    _VERSION = "v1"
    _ACTION: Tuple[Union[str, Callable]] = ("", )

    @classmethod
    def coinToNameSuffix(cls, coin: AbstractCoin):
        return coin.name

    @classmethod
    def addressToNameSuffix(
            cls,
            address: AbstractCoin.Address,
            hd_index: Optional[int] = None):
        value = "{}:{}".format(address.coin.name, address.name)
        if hd_index is not None:
            value += cls.nameSubSuffix("hd_index", hd_index)
        return value

    @classmethod
    def nameSubSuffix(cls, key: str, value: Union[str, int]) -> str:
        if key:
            return ":{}={}".format(key, value)
        return ":{}".format(value)

    @property
    def url(self) -> Optional[str]:
        path_list = []
        for v in self._ACTION:
            if isinstance(v, str):
                path_list.append(v)
            elif callable(v):
                path_list.append(v(self))
            else:
                assert ValueError
        return urlJoin(super().url, self._VERSION, *path_list)

    @property
    def jsonContent(self) -> Optional[dict]:
        assert self.method == self.Method.POST
        (type_, data) = self._createData()
        return {
            "data": {
                "type": type_,
                "attributes": data,
            }
        }

    def _createData(self) -> Tuple[str, Any]:
        return "", None

    def _processResponse(self, response: Optional[dict]) -> None:
        try:
            if response is None:
                self._logger.debug("Empty response.")
                self._processData(None, None, None)
                return

            meta = ResponseMetaParser()
            meta(response)
            if meta.isSlowResponse:
                self._logger.warning(
                    "Server response has taken more than %i seconds.",
                    meta.timeframeSeconds)
            del meta

            ResponseParser()(
                response,
                self._processData,
                self._processError)
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
            value: Optional[dict]) -> None:
        raise NotImplementedError


class AbstractOffsetIteratorApiQuery(AbstractApiQuery):
    _BEST_OFFSET_NAME: Final = "best"
    _BASE_OFFSET_NAME: Final = "base"

    class Mode(Enum):
        FULL = auto()
        FRESH = auto()
        STALE = auto()

    class InitialData:
        def __init__(self, *, first_offset: str, last_offset: str) -> None:
            self._first_offset = first_offset
            self._last_offset = last_offset

        def __eq__(
                self,
                other: AbstractOffsetIteratorApiQuery.InitialData) -> bool:
            return (
                isinstance(other, self.__class__)
                and self._first_offset == other._first_offset
                and self._last_offset == other._last_offset
            )

        @property
        def firstOffset(self) -> str:
            return self._first_offset

        def setActualFirstOffset(self, value: str) -> bool:
            best_value = AbstractOffsetIteratorApiQuery._BEST_OFFSET_NAME
            if self._first_offset == best_value:
                self._first_offset = value
                return True
            return False

        @property
        def lastOffset(self) -> str:
            return self._last_offset

        @property
        def lastOffsetIsBase(self) -> bool:
            base_value = AbstractOffsetIteratorApiQuery._BASE_OFFSET_NAME
            return self._last_offset == base_value

    def __init__(
            self,
            *args,
            mode: Mode,
            first_offset: Optional[str] = None,
            last_offset: Optional[str] = None,
            _initial_data: Optional[InitialData] = None,
            name_suffix: str,
            **kwargs) -> None:
        name_suffix += \
            self.nameSubSuffix("mode", mode.name) \
            + self.nameSubSuffix(
                "first_offset",
                first_offset or self._BEST_OFFSET_NAME) \
            + self.nameSubSuffix(
                "last_offset",
                last_offset or self._BASE_OFFSET_NAME)

        super().__init__(
            *args,
            name_suffix=name_suffix,
            **kwargs)
        self._mode = mode
        self._first_offset = first_offset or self._BEST_OFFSET_NAME
        self._last_offset = last_offset or self._BASE_OFFSET_NAME

        if _initial_data is None:
            self._initial_data = self.InitialData(
                first_offset=self._first_offset,
                last_offset=self._last_offset)
        else:
            self._initial_data = _initial_data

    def isEqualQuery(self, other: AbstractOffsetIteratorApiQuery) -> bool:
        raise NotImplementedError

    @property
    def arguments(self) -> Dict[str, Union[int, str]]:
        return {
            "first_offset": self._first_offset,
            "last_offset": self._last_offset
        }

    @property
    def skip(self) -> bool:
        if (
                self._first_offset == self._BASE_OFFSET_NAME
                or self._first_offset == self._last_offset
        ):
            return True
        return super().skip

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        raise NotImplementedError


class SysinfoApiQuery(AbstractApiQuery):
    _ACTION = ("sysinfo", )

    def __init__(self, coin_list: CoinList) -> None:
        super().__init__(name_suffix=None)
        self._coin_list = coin_list

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = SysinfoParser()
        parser(value, self._DEFAULT_BASE_URL)

        self._logger.info(
            "Server version: %s %s (0x%08x).",
            parser.serverData.get("server_name", "UNKNOWN"),
            parser.serverData.get("server_version_string", "UNKNOWN"),
            parser.serverData.get("server_version", 0xffffffff))

        for coin in self._coin_list:
            coin.serverData = {
                **parser.serverData,
                **parser.serverCoinList.get(coin.name, {})
            }


class CoinsInfoApiQuery(AbstractApiQuery):
    _ACTION = ("coins", )

    def __init__(self, coin_list: CoinList) -> None:
        super().__init__(name_suffix=None)
        self._coin_list = coin_list

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        for coin in self._coin_list:
            parser = CoinsInfoParser()
            if not parser(value, coin.name):
                self._logger.warning(
                    "Coin \"%s\" not found in server response.",
                    coin.name)
                continue
            coin.status = parser.status
            coin.deserialize(coin, **parser.deserializedData)


class AddressInfoApiQuery(AbstractApiQuery):
    _ACTION = (
        "coins",
        lambda self: self._address.coin.name,
        lambda self: self._address.name)

    def __init__(
            self,
            address: AbstractCoin.Address,
            *,
            name_suffix: Optional[str] = None) -> None:
        super().__init__(
            name_suffix=name_suffix or self.addressToNameSuffix(address))
        self._address = address

    def isEqualQuery(self, other: AddressInfoApiQuery) -> bool:
        return (
                super().isEqualQuery(other)
                and self._address.coin.name == other._address.coin.name
                and self._address.name == other._address.name
        )

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = AddressInfoParser()
        parser(value)
        self._address.amount = parser.amount
        self._address.txCount = parser.txCount


class HdAddressIteratorApiQuery(AddressInfoApiQuery):
    def __init__(
            self,
            coin: AbstractCoin,
            *,
            _hd_iterator: Optional[HdAddressIterator] = None,
            _current_address: Optional[AbstractCoin.Address] = None) -> None:
        if _hd_iterator is None:
            _hd_iterator = HdAddressIterator(coin)
        if _current_address is None:
            _current_address = next(_hd_iterator)
        super().__init__(
            _current_address,
            name_suffix=self.addressToNameSuffix(
                _current_address,
                _hd_iterator.currentHdIndex))
        self._hd_iterator = _hd_iterator

    def isEqualQuery(self, other: HdAddressIteratorApiQuery) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._hd_iterator.coin.name == other._hd_iterator.coin.name
        )

    @property
    def skip(self) -> bool:
        if self._hd_iterator.coin.hdPath is None:
            return True
        return super().skip

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        AddressInfoApiQuery._processData(self, data_id, data_type, value)
        if self.statusCode != 200 or value is None:
            return

        if self._address.txCount == 0 and self._address.amount == 0:
            self._hd_iterator.markLastAddress(True)
        else:
            self._hd_iterator.markLastAddress(False)
            self._address.coin.appendAddress(self._address)

        try:
            next_address = next(self._hd_iterator)
        except StopIteration:
            self._logger.debug(
                "HD iteration was finished for coin \"%s\".",
                self._address.coin.name)
            return

        self._next_query = self.__class__(
            self._address.coin,
            _hd_iterator=self._hd_iterator,
            _current_address=next_address)


class AddressTxIteratorApiQuery(
        AbstractOffsetIteratorApiQuery,
        AddressInfoApiQuery):
    _ACTION = AddressInfoApiQuery._ACTION + ("history", )

    def __init__(
            self,
            address: AbstractCoin.Address,
            *,
            mode: AbstractOffsetIteratorApiQuery.Mode,
            first_offset: Optional[str] = None,
            last_offset: Optional[str] = None,
            _initial_data: Optional[
                AbstractOffsetIteratorApiQuery.InitialData] = None):
        super().__init__(
            address,
            name_suffix=self.addressToNameSuffix(address),
            mode=mode,
            first_offset=first_offset,
            last_offset=last_offset,
            _initial_data=_initial_data)

        if self.skip and self._mode == self.Mode.FULL:
            self._next_query = self._createStaleQuery()

    def isEqualQuery(self, other: AddressTxIteratorApiQuery) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._address.coin.name == other._address.coin.name
                and self._address.name == other._address.name
        )

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = AddressTxParser()
        parser(value)

        for tx in parser.txList:
            tx_d = self._address.coin.Tx.deserialize(self._address.coin, **tx)
            if tx_d is not None:
                self._address.appendTx(tx_d)
            else:
                self._logger.warning(
                    "Failed to deserialize transaction '%s'.",
                    tx.get("name", "unnamed"))

        self._initial_data.setActualFirstOffset(parser.firstOffset)
        self._updateAddressHistoryOffsets(parser.firstOffset, parser.lastOffset)

        if parser.lastOffset:
            self._next_query = self.__class__(
                self._address,
                mode=self._mode,
                first_offset=parser.lastOffset,
                last_offset=self._last_offset,
                _initial_data=self._initial_data)
        elif self._mode == self.Mode.FULL:
            self._next_query = self._createStaleQuery()

    def _createStaleQuery(self) -> AddressTxIteratorApiQuery:
        assert self._mode == self.Mode.FULL
        query = self.__class__(
            self._address,
            mode=self.Mode.STALE,
            first_offset=self._address.historyLastOffset,
            last_offset=None,
            _initial_data=self._initial_data)
        return None if query.skip else query

    def _updateAddressHistoryOffsets(
            self,
            first_offset: str,
            last_offset: Optional[str]) -> None:
        is_final_query = not last_offset
        if is_final_query:
            last_offset = self._initial_data.lastOffset

        # address without history
        if (
                not self._address.historyFirstOffset
                and not self._address.historyLastOffset
        ):
            self._address.historyFirstOffset = first_offset
            self._address.historyLastOffset = last_offset
            return

        if self._mode in (self.Mode.FULL, self._mode == self.Mode.FRESH):
            if is_final_query:
                self._address.historyFirstOffset = \
                    self._initial_data.firstOffset
            if self._initial_data.lastOffsetIsBase:
                self._address.historyLastOffset = last_offset

        elif self._mode == self.Mode.STALE:
            if is_final_query or self._initial_data.lastOffsetIsBase:
                self._address.historyLastOffset = last_offset


class AddressUtxoIteratorApiQuery(
        AbstractOffsetIteratorApiQuery,
        AddressInfoApiQuery):
    _ACTION = AddressInfoApiQuery._ACTION + ("unspent", )

    def __init__(
            self,
            address: AbstractCoin.Address,
            *,
            first_offset: Optional[str] = None,
            last_offset: Optional[str] = None,
            _utxo_list: Optional[List[AbstractCoin.Tx.Utxo]] = None) -> None:
        super().__init__(
            address,
            name_suffix=self.addressToNameSuffix(address),
            mode=AbstractOffsetIteratorApiQuery.Mode.FULL,
            first_offset=first_offset,
            last_offset=last_offset)
        self._utxo_list = _utxo_list or []

    def isEqualQuery(self, other: AddressTxIteratorApiQuery) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._mode == other._mode
                and self._address.coin.name == other._address.coin.name
                and self._address.name == other._address.name
        )

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = AddressUtxoParser()
        parser(value)

        for tx in parser.txList:
            tx_d = self._address.coin.Tx.Utxo.deserialize(
                self._address.coin,
                **tx)
            if tx_d is not None:
                self._utxo_list.append(tx_d)
            else:
                self._logger.warning(
                    "Failed to deserialize UTXO '%s:%i'.",
                    tx.get("name", "unnamed"),
                    tx.get("index", -1))

        if parser.lastOffset is None:
            self._address.utxoList = self._utxo_list
        else:
            self._next_query = self.__class__(
                self._address,
                first_offset=parser.lastOffset,
                last_offset=None,
                _utxo_list=self._utxo_list)


class CoinMempoolIteratorApiQuery(AbstractApiQuery):
    _ACTION = (
        "coins",
        lambda self: self._coin.name,
        "unconfirmed")
    _DEFAULT_METHOD = AbstractApiQuery.Method.POST
    ADDRESS_COUNT_PER_REQUEST: Final = 50  # TODO dynamic

    def __init__(
            self,
            coin: AbstractCoin,
            *,
            _address_list: List[Dict[str, Any]] = None) -> None:
        super().__init__(name_suffix=self.coinToNameSuffix(coin))
        self._coin = coin
        self._local_hash = b""
        if _address_list is None:
            self._address_list = self._coin.createMempoolAddressLists(
                self.ADDRESS_COUNT_PER_REQUEST)
        else:
            self._address_list = _address_list

    def isEqualQuery(self, other: CoinMempoolIteratorApiQuery) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin.name == other._coin.name
        )

    @property
    def skip(self) -> bool:
        if len(self._address_list) <= 0:
            self._logger.debug("Address list is empty.")
            return True
        return super().skip

    def _createData(self) -> Tuple[str, Any]:
        current_list = self._address_list.pop(0)
        self._local_hash = current_list["local_hash"]
        data = {
            "address_list": current_list["list"]
        }

        if current_list["remote_hash"]:
            data["last_hash"] = current_list["remote_hash"]

        return "unconfirmed", data

    def _processTx(self, tx: DeserializedData) -> None:
        for tx_io in itertools.chain(tx["input_list"], tx["output_list"]):
            address = self._coin.findAddressByName(tx_io["address_name"])
            if address is None:
                continue

            tx_d = self._coin.Tx.deserialize(self._coin, **tx)
            if tx_d is not None:
                address.appendTx(tx_d)
            else:
                self._logger.warning(
                    "Failed to deserialize unconfirmed transaction '%s'.",
                    tx.get("name", "unnamed"))

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode == 200 and value is not None:
            parser = CoinMempoolParser()
            parser(value)

            for tx in parser.txList:
                self._processTx(tx)
            self._coin.setMempoolAddressListResult(
                self._local_hash,
                parser.hash)
        elif self.statusCode != 304:
            return

        if len(self._address_list) > 0:
            self._next_query = self.__class__(
                self._coin,
                _address_list=self._address_list)


class TxBroadcastApiQuery(AbstractApiQuery):
    _ACTION = (
        "coins",
        lambda self: self._tx.coin.name,
        "tx"
    )
    _DEFAULT_METHOD = AbstractApiQuery.Method.POST

    def __init__(self, tx: Mtx) -> None:
        super().__init__(name_suffix=self.coinToNameSuffix(tx.coin))
        self._tx = tx

    def isEqualQuery(self, other: TxBroadcastApiQuery) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._tx.coin.name == other._tx.coin.name
                and self._tx.to_hex() == other._tx.to_hex()
        )

    def _createData(self) -> Tuple[str, Any]:
        return "tx_broadcast", {
            "data": self._tx.to_hex()
        }

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = BroadcastTxParser()
        parser(value)

        self._logger.info(
            "Transaction \"%s\" broadcasted successfully!",
            parser.txName)
