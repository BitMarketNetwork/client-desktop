# JOK++
from __future__ import annotations

from enum import Flag, auto
from typing import Any, List, Optional, Type

from ..coins.address import AbstractAddress
from ..coins.coin import AbstractCoin
from ..coins.tx import AbstractTx
from ..logger import Logger


class ParseError(LookupError):
    pass


class AbstractServerParser:
    class ParseFlag(Flag):
        NONE = auto()

    def __init__(self, flags=ParseFlag.NONE) -> None:
        self._logger = Logger.getClassLogger(__name__, self.__class__)
        self._flags = flags

    @classmethod
    def _parse(
            cls,
            item: dict,
            key_name: str,
            value_type: Type,
            default_value: Any = None) -> Any:
        try:
            value = value_type(item[key_name])
        except KeyError:
            if default_value is None:
                raise ParseError("Key \"{}\" not found.".format(key_name))
            value = default_value
        except (TypeError, ValueError):
            raise ParseError("Invalid value for key \"{}\".".format(key_name))
        return value


class ServerCoinParser(AbstractServerParser):
    def parse(self, response: dict, coin: AbstractCoin) -> bool:
        try:
            offset = self._parse(response, "offset", str)
            unverified_offset = self._parse(response, "unverified_offset", str)
            unverified_hash = self._parse(response, "unverified_hash", str)
            height = self._parse(response, "height", int)
            verified_height = self._parse(response, "verified_height", int)
            status = self._parse(response, "status", int)
        except ParseError as e:
            self._logger.error(
                "Failed to parse coin \"{}\": {}"
                .format(coin.fullName, str(e)))
            return False

        # TODO legacy order
        coin.status = status
        coin.unverifiedHash = unverified_hash
        coin.unverifiedOffset = unverified_offset
        coin.offset = offset
        coin.verifiedHeight = verified_height
        coin.height = height
        return True


class ServerTxParser(AbstractServerParser):
    class ParseFlag(Flag):
        NONE = auto()
        MEMPOOL = auto()

    def __init__(self, flags=ParseFlag.NONE) -> None:
        super().__init__(flags=flags)

    def parseList(
            self,
            response: dict,
            address: AbstractAddress) -> Optional[List[AbstractTx]]:
        if not isinstance(response, dict):
            self._logger.error(
                "Invalid transaction list response for address \"{}\"."
                .format(address.name))
            return None

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
            data = {
                "name": name,  # TODO validate name
                "height": self._parse(
                    response,
                    "height",
                    int,
                    -1 if self._flags & self.ParseFlag.MEMPOOL else None),
                "time": self._parse(response, "time", int),
                "amount": self._parse(response, "amount", int),
                "fee": self._parse(response, "fee", int),
                "coinbase": self._parse(response, "coinbase", int) != 0,
                "input_list": [self._parseIo(v) for v in response["input"]],
                "output_list": [self._parseIo(v) for v in response["output"]]
            }
        except ParseError as e:
            self._logger.error(
                "Failed to parse transaction for address \"{}\": {}"
                .format(address.name, str(e)))
            return None

        tx = AbstractTx.deserialize(address, **data)
        address.appendTx(tx)
        return tx

    @classmethod
    def _parseIo(cls, item: dict) -> dict:
        try:
            return {
                "output_type": cls._parse(item, "output_type", str),
                "address_type": cls._parse(item, "type", str),
                "address_name": cls._parse(item, "address", str),
                "amount": cls._parse(item, "amount", int)
            }
        except ParseError as e:
            raise ParseError(
                "Failed to parse transaction IO: {}"
                .format(str(e)))
