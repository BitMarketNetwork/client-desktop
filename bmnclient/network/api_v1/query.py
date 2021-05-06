# JOK4
from __future__ import annotations

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
    from ..query_manager import NetworkQueryManager
    from ...coins.abstract.coin import AbstractCoin
    from ...coins.list import CoinList
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
    def addressToNameSuffix(cls, address: AbstractCoin.Address):
        return "{}:{}".format(address.coin.name, address.name)

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


class AbstractIteratorApiQuery(AbstractApiQuery):
    def __init__(
            self,
            *args,
            query_manager: NetworkQueryManager,
            finished_callback: Optional[
                Callable[[AbstractApiQuery], None]] = None,
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._query_manager = query_manager
        self._finished_callback = finished_callback
        self._next_query: Optional[AbstractApiQuery] = None

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        raise NotImplementedError

    def _onResponseFinished(self) -> None:
        super()._onResponseFinished()
        if self._next_query is None:
            if self._finished_callback is not None:
                self._finished_callback(self)
        else:
            self._query_manager.put(self._next_query)


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

            coin.beginUpdateState()
            if True:
                coin.status = parser.status
                coin.unverifiedHash = parser.unverifiedHash
                coin.unverifiedOffset = parser.unverifiedOffset
                coin.offset = parser.offset
                coin.verifiedHeight = parser.verifiedHeight
                coin.height = parser.height
            coin.endUpdateState()


class AddressInfoApiQuery(AbstractApiQuery):
    _ACTION = (
        "coins",
        lambda self: self._address.coin.name,
        lambda self: self._address.name)

    def __init__(
            self,
            address: AbstractCoin.Address,
            *,
            name_suffix: Optional[str] = None,
            **kwargs) -> None:
        super().__init__(
            name_suffix=name_suffix or self.addressToNameSuffix(address),
            **kwargs)
        self._address = address

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


class HdAddressIteratorApiQuery(AddressInfoApiQuery, AbstractIteratorApiQuery):
    def __init__(
            self,
            coin: AbstractCoin,
            *,
            query_manager: NetworkQueryManager,
            finished_callback: Optional[
                Callable[[HdAddressIteratorApiQuery], None]] = None,
            _hd_iterator: Optional[HdAddressIterator] = None,
            _current_address: Optional[AbstractCoin.Address] = None) -> None:
        if _hd_iterator is None:
            _hd_iterator = HdAddressIterator(coin)
        if _current_address is None:
            _current_address = next(_hd_iterator)
        super().__init__(
            _current_address,
            query_manager=query_manager,
            finished_callback=finished_callback)
        self._hd_iterator = _hd_iterator

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        super()._processData(data_id, data_type, value)
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
            query_manager=self._query_manager,
            finished_callback=self._finished_callback,
            _hd_iterator=self._hd_iterator,
            _current_address=next_address)


class AddressTxIteratorApiQuery(AddressInfoApiQuery, AbstractIteratorApiQuery):
    _ACTION = AddressInfoApiQuery._ACTION + ("history", )
    _BEST_OFFSET_NAME: Final = "best"
    _BASE_OFFSET_NAME: Final = "base"

    def __init__(
            self,
            address: AbstractCoin.Address,
            *,
            query_manager: NetworkQueryManager,
            finished_callback: Optional[
                Callable[[HdAddressIteratorApiQuery], None]] = None,
            first_offset: Optional[str] = None,
            last_offset: Optional[str] = None) -> None:
        super().__init__(
            address,
            query_manager=query_manager,
            finished_callback=finished_callback)
        self._first_offset = first_offset
        self._last_offset = last_offset

    @property
    def arguments(self) -> Dict[str, Union[int, str]]:
        return {
            "first_offset": self._first_offset or self._BEST_OFFSET_NAME,
            "last_offset": self._last_offset or self._BASE_OFFSET_NAME,
        }

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = AddressTxParser(self._address)
        parser(value)

        for tx in parser.txList:
            self._address.appendTx(tx)

        # if scan from "best", save real offset
        if not self._first_offset:
            self._address.historyFirstOffset = parser.firstOffset

        if parser.lastOffset:
            self._address.historyLastOffset = parser.lastOffset
        else:
            self._address.historyLastOffset = self._BASE_OFFSET_NAME

        if parser.lastOffset is not None:
            self._next_query = self.__class__(
                self._address,
                query_manager=self._query_manager,
                finished_callback=self._finished_callback,
                first_offset=parser.lastOffset,
                last_offset=None)


class AddressUtxoIteratorApiQuery(AddressTxIteratorApiQuery):
    _ACTION = AddressInfoApiQuery._ACTION + ("unspent", )

    def __init__(
            self,
            address: AbstractCoin.Address,
            *,
            query_manager: NetworkQueryManager,
            finished_callback: Optional[
                Callable[[HdAddressIteratorApiQuery], None]] = None,
            first_offset: Optional[str] = None,
            last_offset: Optional[str] = None,
            _utxo_list: Optional[List[AbstractCoin.Tx.Utxo]] = None) -> None:
        super().__init__(
            address,
            query_manager=query_manager,
            finished_callback=finished_callback,
            first_offset=first_offset,
            last_offset=last_offset)
        self._utxo_list = _utxo_list or []

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = AddressUtxoParser(self._address)
        parser(value)
        self._utxo_list.extend(parser.txList)

        if parser.lastOffset is None:
            self._address.utxoList = self._utxo_list
        else:
            self._next_query = self.__class__(
                self._address,
                query_manager=self._query_manager,
                finished_callback=self._finished_callback,
                first_offset=parser.lastOffset,
                last_offset=None,
                _utxo_list=self._utxo_list)


class CoinMempoolIteratorApiQuery(AbstractIteratorApiQuery):
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
            query_manager: NetworkQueryManager,
            finished_callback: Optional[Callable[
                [CoinMempoolIteratorApiQuery], None]] = None,
            _address_list: List[Dict[str, Any]] = None) -> None:
        super().__init__(
            query_manager=query_manager,
            finished_callback=finished_callback,
            name_suffix=self.coinToNameSuffix(coin))
        self._coin = coin
        self._local_hash = b""
        if _address_list is None:
            self._address_list = self._coin.createMempoolAddressLists(
                self.ADDRESS_COUNT_PER_REQUEST)
        else:
            self._address_list = _address_list

    @property
    def skip(self) -> bool:
        if not super().skip:
            if len(self._address_list) > 0:
                return False
            self._logger.debug("Address list is empty.")
        return True

    def _createData(self) -> Tuple[str, Any]:
        current_list = self._address_list.pop(0)
        self._local_hash = current_list["local_hash"]
        data = {
            "address_list": current_list["list"]
        }

        if current_list["remote_hash"]:
            data["last_hash"] = current_list["remote_hash"]

        return "unconfirmed", data

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode == 200 and value is not None:
            parser = CoinMempoolParser(self._coin)
            parser(value)

            for tx in parser.txList:
                tx.address.appendTx(tx)
            self._coin.setMempoolAddressListResult(
                self._local_hash,
                parser.hash)
        elif self.statusCode != 304:
            return

        if len(self._address_list) > 0:
            self._next_query = self.__class__(
                self._coin,
                query_manager=self._query_manager,
                finished_callback=self._finished_callback,
                _address_list=self._address_list)


class TxBroadcastApiQuery(AbstractApiQuery):
    _ACTION = (
        "coins",
        lambda self: self._tx.coin.name,
        "tx"
    )
    _DEFAULT_METHOD = AbstractApiQuery.Method.POST

    def __init__(self, tx: Mtx) -> None:
        super().__init__(
            name_suffix=self.coinToNameSuffix(tx.coin))
        self._tx = tx

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
