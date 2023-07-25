from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

from ...coins.abstract import Coin
from ...config import ConfigStaticList
from ...logger import Logger
from ...utils.class_property import classproperty
from ..utils import NetworkUtils

if TYPE_CHECKING:
    from typing import Dict, Final, Iterator, Optional, Type, Union

    from ...application import CoreApplication


class AbstractBlockchainExplorer:
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _URL_MAP: Dict[str, str] = {}
    _COIN_MAP: Dict[str, str] = {}

    def __init__(self) -> None:
        self._logger = Logger.classLogger(self.__class__)

    @classproperty
    def name(self) -> str:
        return self._SHORT_NAME

    @classproperty
    def fullName(self) -> str:
        return self._FULL_NAME

    def browse(self, object_: Union[Coin, Coin.Address, Coin.Tx]) -> bool:
        request_name = ""
        url = ""
        values = dict(coin_name="", address_name="", tx_name="")

        if isinstance(object_, Coin):
            request_name = "Coin"
            url = self._URL_MAP.get("coin")
            values["coin_name"] = self._COIN_MAP.get(object_.name)
        elif isinstance(object_, Coin.Address):
            request_name = "Address"
            url = self._URL_MAP.get("address")
            values["coin_name"] = self._COIN_MAP.get(object_.coin.name)
            values["address_name"] = object_.name
        elif isinstance(object_, Coin.Tx):
            request_name = "Transaction"
            url = self._URL_MAP.get("tx")
            values["coin_name"] = self._COIN_MAP.get(object_.coin.name)
            values["tx_name"] = object_.name

        if not url or None in values.items():
            self._logger.error(
                "%s request not supported by '%s'.",
                request_name,
                self._FULL_NAME,
            )
            return False

        values = {
            k: NetworkUtils.quoteUrlQueryItem(v) for k, v in values.items()
        }
        url = url.format(**values)
        self._logger.debug("%s request URL: %s", request_name, url)

        try:
            webbrowser.open(url)
        except webbrowser.Error as e:
            self._logger.error(
                "Failed to open Web Browser for %s request:"
                "\n\tURL: %s\n\tError: %s",
                request_name,
                url,
                str(e),
            )
            return False
        return True


class BlockchainComExplorer(AbstractBlockchainExplorer):
    _SHORT_NAME: Final = "blockchain"
    _FULL_NAME: Final = "Blockchain.com"
    _URL_MAP: Final = {
        "coin": "https://www.blockchain.com/explorer?view={coin_name}",
        "address": "https://www.blockchain.com/{coin_name}/address/{address_name}",
        "tx": "https://www.blockchain.com/{coin_name}/tx/{tx_name}",
    }
    _COIN_MAP: Final = {"btc": "btc", "btctest": "btc-testnet", "ltc": "ltc"}


class BlockchainExplorerList(ConfigStaticList):
    def __init__(self, application: CoreApplication) -> None:
        super().__init__(
            application.config,
            application.config.Key.SERVICES_BLOCKCHAIN_EXPLORER,
            (BlockchainComExplorer,),
            default_index=0,
            item_property="name",
        )
        self._logger.debug(
            "Current blockchain explorer: %s", self.current.fullName
        )

    def __iter__(self) -> Iterator[Type[AbstractBlockchainExplorer]]:
        return super().__iter__()

    def __getitem__(
        self, value: Union[str, int]
    ) -> Optional[Type[AbstractBlockchainExplorer]]:
        return super().__getitem__(value)

    @property
    def current(self) -> Type[AbstractBlockchainExplorer]:
        return super().current
