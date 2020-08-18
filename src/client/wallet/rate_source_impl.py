import abc
import logging
from typing import Union
log = logging.getLogger(__name__)


class RateSourceWorkerBase(abc.ABC):
    api_url = None
    action = None

    @abc.abstractmethod
    def get_arguments(self, coins: list, currencies: Union[list, str]) -> dict:
        ...

    @abc.abstractmethod
    def process_result(self, coins: list, currencies: Union[list, str], table: dict) -> None:
        ...


class CoinGeckoWorker(RateSourceWorkerBase):
    api_url = "https://api.coingecko.com/api/v3/simple/"
    action = "price"

    def get_arguments(self, coins: list, currencies: Union[list, str]) -> dict:
        return {
            "ids": ",".join([c.basename for c in coins]),
            "vs_currencies": currencies,
        }

    def process_result(self, coins: list, currencies: Union[list, str], table: dict) -> None:
        for coin in coins:
            coin.rate = table[coin.basename][currencies]

# NOT READY!!!
class CoinMarkerCapWorker(RateSourceWorkerBase):
    api_url = "https://api.coingecko.com/api/v3/simple/"
    action = "price"
    API_KEY = "4fbeacd1-a952-4770-8e8e-3e40344ffb62"

    def get_arguments(self, coins: list, currencies: Union[list, str]) -> dict:
        return {
            "ids": ",".join([c.basename for c in coins]),
            "vs_currencies": currencies,
        }

    def process_result(self, coins: list, currencies: Union[list, str], table: dict) -> None:
        for coin in coins:
            coin.rate = table[coin.basename][currencies]


class CoinLayerWorker(RateSourceWorkerBase):
    api_url = "http://api.coinlayer.com/api/"
    action = "live"
    API_KEY = "e38a4af7a90106ae330da4cafe9123c1"

    def get_arguments(self, coins: list, currencies: Union[list, str]) -> dict:
        return {
            "symbols": ",".join([c.unit for c in coins]),
            "access_key": self.API_KEY,
            "target": currencies,
        }

    def process_result(self, coins: list, currencies: Union[list, str], table: dict) -> None:
        log.debug(f"==> {table}")
        if table["success"]:
            rates = table["rates"]
            # only for USD
            for coin in coins:
                rate = rates.get(coin.unit,None)
                if rate:
                    coin.rate = rate
                    log.debug(f"{coin} === {coin.rate}")
