# JOK++
from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING

from .parser import \
    AddressHistoryParser, \
    AddressInfoParser, \
    CoinsInfoParser, \
    ParseError, \
    ResponseParser, \
    ResponseMetaParser, \
    SysinfoParser
from ..query import AbstractJsonQuery
from ..utils import urlJoin
from ...coins.hd import HdAddressIterator
from ...logger import Logger

if TYPE_CHECKING:
    from typing import Callable, Dict, Optional, Union
    from ...application import CoreApplication
    from ...coins.coin import AbstractCoin
    from ...wallet.address import CAddress


class AbstractServerApiQuery(AbstractJsonQuery):
    _DEFAULT_CONTENT_TYPE = "application/vnd.api+json"
    _DEFAULT_BASE_URL = "https://d1.bitmarket.network:30110/"  # TODO dynamic
    _VERSION = "v1"
    _ACTION = ""

    def __init__(
            self,
            application: CoreApplication,
            *,
            name_suffix: Optional[str]) -> None:
        super().__init__(name_suffix=name_suffix)
        self._application = application

    @property
    def url(self) -> Optional[str]:
        return urlJoin(super().url, self._VERSION, self._ACTION)

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


class SysinfoApiQuery(AbstractServerApiQuery):
    _ACTION = "sysinfo"

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


class CoinsInfoApiQuery(AbstractServerApiQuery):
    _ACTION = "coins"

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


class AddressInfoApiQuery(AbstractServerApiQuery):
    _ACTION = "coins"

    def __init__(
            self,
            application: CoreApplication,
            address: CAddress) -> None:
        super().__init__(
            application,
            name_suffix="{}:{}".format(address.coin.shortName, address.name))
        self._address = address

    @property
    def url(self) -> Optional[str]:
        return urlJoin(
            super().url,
            self._address.coin.shortName,
            self._address.name)

    def _processData(
            self,
            data_id: Optional[str],
            data_type: Optional[str],
            value: Optional[dict]) -> None:
        if self.statusCode != 200 or value is None:
            return
        print(value)

class HdAddressIteratorApiQuery(AddressInfoApiQuery):
    def __init__(
            self,
            application: CoreApplication,
            coin: AbstractCoin,
            *,
            finished_callback: Callable[
                [HdAddressIteratorApiQuery], None] = None,
            _hd_iterator: Optional[HdAddressIterator] = None,
            _current_address: Optional[CAddress] = None) -> None:
        if _hd_iterator is None:
            _hd_iterator = HdAddressIterator(coin)
        if _current_address is None:
            _current_address = next(_hd_iterator)
        super().__init__(application, _current_address)
        self._hd_iterator = _hd_iterator
        self._finished_callback = finished_callback
        self._next_query: Optional[HdAddressIteratorApiQuery] = None

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
            self._application.networkQueryManager.put(TxIteratorApiQuery(
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

    def _onResponseFinished(self) -> None:
        super()._onResponseFinished()
        if self._next_query is None:
            self._finished_callback(self)
        else:
            self._application.networkQueryManager.put(self._next_query)
