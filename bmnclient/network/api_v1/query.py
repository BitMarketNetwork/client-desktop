# JOK++
from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING

from .parser import \
    AddressInfoParser, \
    AddressTxParser, \
    AddressUnspentParser, \
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
    from ...application import CoreApplication
    from ...coins.coin import AbstractCoin
    from ...wallet.address import CAddress


class AbstractApiQuery(AbstractJsonQuery):
    _DEFAULT_CONTENT_TYPE = "application/vnd.api+json"
    _DEFAULT_BASE_URL = "https://d1.bitmarket.network:30110/"  # TODO dynamic
    _VERSION = "v1"
    _ACTION: Tuple[Union[str, Callable]] = ("", )

    def __init__(
            self,
            application: CoreApplication,
            *args,
            name_suffix: Optional[str],
            **kwargs) -> None:
        super().__init__(name_suffix=name_suffix)
        self._application = application

    @classmethod
    def coinToNameSuffix(cls, coin: AbstractCoin):
        return coin.shortName

    @classmethod
    def addressToNameSuffix(cls, address: CAddress):
        return "{}:{}".format(address.coin.shortName, address.name)

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
            application: CoreApplication,
            *args,
            finished_callback: Optional[
                Callable[[AbstractApiQuery], None]] = None,
            **kwargs) -> None:
        super().__init__(application, *args, **kwargs)
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
            self._application.networkQueryManager.put(self._next_query)


class SysinfoApiQuery(AbstractApiQuery):
    _ACTION = ("sysinfo", )

    def __init__(self, application: CoreApplication) -> None:
        super().__init__(application, name_suffix=None)

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

        for coin in self._application.coinList:
            coin.serverData = {
                **parser.serverData,
                **parser.serverCoinList.get(coin.shortName, {})
            }


class CoinsInfoApiQuery(AbstractApiQuery):
    _ACTION = ("coins", )

    def __init__(self, application: CoreApplication) -> None:
        super().__init__(application, name_suffix=None)

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        for coin in self._application.coinList:
            state_hash = coin.stateHash
            parser = CoinsInfoParser()
            if not parser(value, coin.shortName):
                self._logger.warning(
                    "Coin \"%s\" not found in server response.",
                    coin.shortName)
                continue

            # TODO legacy order
            coin.status = parser.status
            coin.unverifiedHash = parser.unverifiedHash
            coin.unverifiedOffset = parser.unverifiedOffset
            coin.offset = parser.offset
            coin.verifiedHeight = parser.verifiedHeight
            coin.height = parser.height

            if coin.stateHash == state_hash:
                continue

            self._logger.debug("Coin state was changed, updating addresses...")
            # TODO
            # self._application.databaseThread.saveCoin.emit(coin)
            # for address in coin.addressList:
            #     self._application.networkQueryManager.put(
            #            AddressInfoApiQuery(self._application, address))
            #     AddressHistoryCommand()


class AddressInfoApiQuery(AbstractApiQuery):
    _ACTION = (
        "coins",
        lambda self: self._address.coin.shortName,
        lambda self: self._address.name)

    def __init__(
            self,
            application: CoreApplication,
            address: CAddress,
            *args,
            name_suffix: Optional[str] = None,
            **kwargs) -> None:
        super().__init__(
            application,
            *args,
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

        # TODO
        # if balance != self._address.amount or \
        #        txCount != self._address.txCount or \
        #        type_ != self._address.type:
        #    self._address.type = type_
        #    databaseThread.save_address(self._address)
        #    diff = txCount - self._address.realTxCount
        #    if diff > 0 and not self._address.is_going_update:
        #        log.debug("Need to download more %s tx for %s",
        #                  diff, self._address)
        #       AddressHistoryCommand(self._address, parent=self)


class HdAddressIteratorApiQuery(AddressInfoApiQuery, AbstractIteratorApiQuery):
    def __init__(
            self,
            application: CoreApplication,
            coin: AbstractCoin,
            *,
            finished_callback: Optional[
                Callable[[HdAddressIteratorApiQuery], None]] = None,
            _hd_iterator: Optional[HdAddressIterator] = None,
            _current_address: Optional[CAddress] = None) -> None:
        if _hd_iterator is None:
            _hd_iterator = HdAddressIterator(coin)
        if _current_address is None:
            _current_address = next(_hd_iterator)
        super().__init__(
            application,
            _current_address,
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

            # TODO tmp
            self._application.networkQueryManager.put(
                AddressTxIteratorApiQuery(
                    self._application,
                    self._address))
            self._application.networkQueryManager.put(
                AddressUnspentIteratorApiQuery(
                    self._application,
                    self._address))

        try:
            next_address = next(self._hd_iterator)
        except StopIteration:
            self._logger.debug(
                "HD iteration was finished for coin \"%s\".",
                self._address.coin.shortName)
            return

        self._next_query = self.__class__(
            self._application,
            self._address.coin,
            finished_callback=self._finished_callback,
            _hd_iterator=self._hd_iterator,
            _current_address=next_address)


class AddressTxIteratorApiQuery(AddressInfoApiQuery, AbstractIteratorApiQuery):
    _ACTION = AddressInfoApiQuery._ACTION + ("history", )
    _BEST_OFFSET_NAME: Final = "best"
    _BASE_OFFSET_NAME: Final = "base"

    def __init__(
            self,
            application: CoreApplication,
            address: CAddress,
            *,
            finished_callback: Optional[
                Callable[[HdAddressIteratorApiQuery], None]] = None,
            first_offset: Optional[str] = None,
            last_offset: Optional[str] = None) -> None:
        super().__init__(
            application,
            address,
            finished_callback=finished_callback)
        self._first_offset = first_offset
        self._last_offset = last_offset

    @property
    def arguments(self) -> Dict[str, Union[int, str]]:
        args = {
            "first_offset": self._first_offset or self._BEST_OFFSET_NAME,
            "last_offset": self._last_offset or self._BASE_OFFSET_NAME,
        }
        if self._application.isDebugMode:
            args["limit"] = randint(0, 52)
        return args

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
            # TODO
            # self._application.databaseThread.database._write_transaction(tx)
            # self._application.uiManager.process_incoming_tx(tx)

        # if scan from "best", save real offset
        if not self._first_offset:
            self._address.historyFirstOffset = parser.firstOffset

        if parser.lastOffset:
            self._address.historyLastOffset = parser.lastOffset
        else:
            self._address.historyLastOffset = self._BASE_OFFSET_NAME

        # TODO
        # self._application.databaseThread.save_address(self._address)

        if parser.lastOffset is not None:
            self._next_query = self.__class__(
                self._application,
                self._address,
                first_offset=parser.lastOffset,
                last_offset=None)


class AddressUnspentIteratorApiQuery(AddressTxIteratorApiQuery):
    _ACTION = AddressInfoApiQuery._ACTION + ("unspent", )

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return

        parser = AddressUnspentParser(self._address)
        parser(value)
        self._address.utxoList = parser.txList

        if parser.lastOffset is not None:
            self._next_query = self.__class__(
                self._application,
                self._address,
                first_offset=parser.lastOffset,
                last_offset=None)


class CoinMempoolIteratorApiQuery(AbstractIteratorApiQuery):
    _ACTION = (
        "coins",
        lambda self: self._coin.shortName,
        "unconfirmed")
    _DEFAULT_METHOD = AbstractApiQuery.Method.POST
    ADDRESS_COUNT_PER_REQUEST: Final = 50  # TODO dynamic
