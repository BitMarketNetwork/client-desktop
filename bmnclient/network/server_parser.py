# JOK++
from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING, Type

from ..logger import Logger
from ..utils.meta import classproperty

from ..coins.address import AbstractAddress
from ..coins.coin import AbstractCoin
from ..coins.tx import AbstractTx

if TYPE_CHECKING:
    import logging


class ParseError(LookupError):
    pass


class AbstractServerParser:
    __logger = None

    @classproperty
    def _logger(cls) -> logging.Logger:  # noqa
        if not cls.__logger:
            cls.__logger = Logger.getClassLogger(__name__, cls)  # noqa
        return cls.__logger

    @classmethod
    def _parse(cls, item: dict, key_name: str, value_type: Type) -> Any:
        try:
            value = value_type(item[key_name])
        except KeyError:
            raise ParseError("Key \"{}\" not found.".format(key_name))
        except (TypeError, ValueError):
            raise ParseError("Invalid value for key \"{}\".".format(key_name))
        return value


class ServerCoinParser(AbstractServerParser):
    @classmethod
    def parse(cls, response: dict, coin: AbstractCoin) -> bool:
        try:
            offset = cls._parse(response, "offset", str)
            unverified_offset = cls._parse(response, "unverified_offset", str)
            unverified_hash = cls._parse(response, "unverified_hash", str)
            height = cls._parse(response, "height", int)
            verified_height = cls._parse(response, "verified_height", int)
            status = cls._parse(response, "status", int)
        except ParseError as e:
            cls._logger.error(
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
    @classmethod
    def parseList(
            cls,
            response: dict,
            address: AbstractAddress) -> Optional[List[AbstractTx]]:
        if not isinstance(response, dict):
            cls._logger.error(
                "Invalid transaction list response for address \"{}\"."
                .format(address.name))
            return None

        result = []
        for (name, value) in response.items():
            tx = cls.parse(name, value, address)
            if tx is None:
                return None
            result.append(tx)
        return result

    @classmethod
    def parse(
            cls,
            name: str,
            response: dict,
            address: AbstractAddress) -> Optional[AbstractTx]:
        try:
            data = {
                "name": name,  # TODO validate name
                "height": cls._parse(response, "height", int),
                "time": cls._parse(response, "time", int),
                "amount": cls._parse(response, "amount", int),
                "fee": cls._parse(response, "fee", int),
                "coinbase": cls._parse(response, "coinbase", int) != 0,
                "input_list": [cls._parseIo(v) for v in response["input"]],
                "output_list": [cls._parseIo(v) for v in response["output"]]
            }
        except ParseError as e:
            cls._logger.error(
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
