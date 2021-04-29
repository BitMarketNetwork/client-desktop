# JOK+++
from __future__ import annotations

from enum import auto, Flag
from typing import TYPE_CHECKING

from ...coins.tx import AbstractTx
from ...logger import Logger

if TYPE_CHECKING:
    from typing import Any, Final, List, Optional, Type, Union
    from ...coins.address import AbstractAddress


class ParseError(LookupError):
    pass


class AbstractParser:
    class ParseFlag(Flag):
        pass

    def __init__(
            self,
            flags: Optional[AbstractParser.ParseFlag] = None) -> None:
        self._logger = Logger.getClassLogger(__name__, self.__class__)
        self._flags = flags

    @classmethod
    def parseKey(
            cls,
            item: Union[dict, list],
            key_name: Union[str, int],
            value_type: Type,
            default_value: Any = None,
            *,
            allow_none=False) -> Any:
        try:
            value = item[key_name]
            if value is None:
                if not allow_none:
                    raise ValueError
            elif not isinstance(value, value_type):
                raise TypeError
            return value
        except (KeyError, IndexError):
            if default_value is not None:
                return default_value
            raise ParseError(
                "key \"{}\" not found".format(str(key_name)))
        except (TypeError, ValueError):
            raise ParseError(
                "invalid value for key \"{}\"".format(str(key_name)))


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
            self._logger.error(
                "Failed to parse transaction for address \"{}\": {}"
                .format(address.name, Logger.exceptionToString(e)))
            return None

        return AbstractTx.deserialize(address, **data)

    @classmethod
    def _parseIo(cls, item: dict) -> dict:
        return {
            "output_type": cls.parseKey(item, "output_type", str),
            "address_type": cls.parseKey(item, "type", str, allow_none=True),
            "address_name": cls.parseKey(item, "address", str, allow_none=True),
            "amount": cls.parseKey(item, "amount", int)
        }
