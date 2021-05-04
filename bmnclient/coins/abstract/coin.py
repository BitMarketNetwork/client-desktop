# JOK4
from __future__ import annotations

import math
from typing import TYPE_CHECKING, TypedDict

from .address import AbstractAddress
from .currency import AbstractCurrency
from .tx import AbstractTx
from ..currency import FiatRate, NoneFiatCurrency
from ...crypto.digest import Sha256Digest
from ...utils.meta import classproperty
from ...utils.serialize import Serializable, serializable
from ...wallet.mutable_tx import MutableTransaction

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Optional, Union
    from ...wallet.hd import HDNode


class AbstractCoinInterface:
    def afterSetHeight(self) -> None:
        raise NotImplementedError

    def afterSetStatus(self) -> None:
        raise NotImplementedError

    def afterSetFiatRate(self) -> None:
        raise NotImplementedError

    def afterRefreshAmount(self) -> None:
        raise NotImplementedError

    def beforeAppendAddress(self, address: AbstractAddress) -> None:
        raise NotImplementedError

    def afterAppendAddress(self, address: AbstractAddress) -> None:
        raise NotImplementedError

    def afterSetServerData(self) -> None:
        raise NotImplementedError


class AbstractCoin(Serializable):
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _IS_TEST_NET = False
    # https://github.com/satoshilabs/slips/blob/master/slip-0044.md
    _BIP0044_COIN_TYPE = -1

    class Currency(AbstractCurrency):
        pass

    class Address(AbstractAddress):
        pass

    class Tx(AbstractTx):
        pass

    class MempoolCacheItem(TypedDict):
        remote_hash: Optional[str]
        access_count: int

    def __init__(
            self,
            *,
            model_factory: Optional[Callable[[object], object]] = None) -> None:
        super().__init__()

        self._model_factory = model_factory
        self.__state_hash = 0

        self._offset = ""
        self._unverified_offset = ""
        self._unverified_hash = ""

        self._height = 0
        self._verified_height = 0

        self._status = 0

        self._fiat_rate = FiatRate(0, NoneFiatCurrency)
        self._amount = 0

        self._hd_path: Optional[HDNode] = None

        self._address_list: List[AbstractCoin.Address] = []
        self._server_data: Dict[str, Union[int, str]] = {}
        self._mempool_cache: Dict[bytes, AbstractCoin.MempoolCacheItem] = {}
        self._mempool_cache_access_counter = 0
        self._mutable_tx = MutableTransaction(self)

        self._model: Optional[AbstractCoinInterface] = self.model_factory(self)

    @property
    def model(self) -> Optional[AbstractCoinInterface]:
        return self._model

    def _updateState(self) -> int:
        old_value = self.__state_hash
        self.__state_hash = (old_value + 1) & ((1 << 64) - 1)
        return old_value

    @property
    def stateHash(self) -> int:
        return self.__state_hash

    def model_factory(self, owner: object) -> Optional[object]:
        if self._model_factory:
            return self._model_factory(owner)
        return None

    @serializable
    @property
    def shortName(cls) -> str:  # noqa  # TODO to name()
        return cls._SHORT_NAME

    @classproperty
    def fullName(cls) -> str:  # noqa
        return cls._FULL_NAME

    @classproperty
    def isTestNet(cls) -> bool:  # noqa
        return cls._IS_TEST_NET

    @classproperty
    def iconPath(cls) -> str:  # noqa
        # relative to "resources/images"
        return "coins/" + cls._SHORT_NAME + ".svg"

    @serializable
    @property
    def offset(self) -> str:
        return self._offset

    @offset.setter
    def offset(self, value: str) -> None:
        if self._offset != value:
            self._update_wallets(self._offset)
            self._offset = value
            self._updateState()

    @serializable
    @property
    def unverifiedOffset(self) -> str:
        return self._unverified_offset

    @unverifiedOffset.setter
    def unverifiedOffset(self, value: str) -> None:
        if self._unverified_offset != value:
            # self._update_wallets(self._offset)
            self._unverified_offset = value
            self._updateState()

    @serializable
    @property
    def unverifiedHash(self) -> str:
        return self._unverified_hash

    @unverifiedHash.setter
    def unverifiedHash(self, value: str) -> None:
        if self._unverified_hash != value:
            if not self._unverified_hash:
                self._update_wallets()
            else:
                self._update_wallets(
                    self._unverified_offset,
                    self._verified_height)
            self._unverified_hash = value
            self._updateState()

    @serializable
    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        if self._height != value:
            self._height = value
            self._updateState()
            if self._model:
                self._model.afterSetHeight()

    @serializable
    @property
    def verifiedHeight(self) -> int:
        return self._verified_height

    @verifiedHeight.setter
    def verifiedHeight(self, value: int) -> None:
        if self._verified_height != value:
            self._verified_height = value
            self._updateState()

    @property
    def status(self) -> int:
        return self._status

    @status.setter
    def status(self, value: int) -> None:
        if self._status != value:
            self._status = value
            # self._updateState()
            if self._model:
                self._model.afterSetStatus()

    @property
    def fiatRate(self) -> FiatRate:
        return self._fiat_rate

    @fiatRate.setter
    def fiatRate(self, fiat_rate: FiatRate) -> None:
        self._fiat_rate = fiat_rate
        if self._model:
            self._model.afterSetFiatRate()

    def toFiatAmount(self, value: Optional[int] = None) -> Optional[int]:
        if value is None:
            value = self._amount
        value *= self._fiat_rate.value
        value //= self.Currency.decimalDivisor
        return value if self._fiat_rate.currency.isValidValue(value) else None

    def fromFiatAmount(self, value: int) -> Optional[int]:
        value *= self.Currency.decimalDivisor
        if self._fiat_rate.value:
            value = math.ceil(value / self._fiat_rate.value)
        else:
            value = 0
        return value if self.Currency.isValidValue(value) else None

    @property
    def amount(self) -> int:
        return self._amount

    def refreshAmount(self) -> None:  # TODO vs refreshUnspent
        a = sum(a.amount for a in self._address_list if not a.readOnly)
        self._amount = a
        if self._model:
            self._model.afterRefreshAmount()

    def refreshUnspent(self) -> None:
        self._mutable_tx.refreshSourceList()

    def makeHdPath(self, purpose_path: HDNode) -> None:
        assert self._hd_path is None
        self._hd_path = purpose_path.make_child_prv(
            self._BIP0044_COIN_TYPE,
            True,
            self.network)

    @property
    def hdPath(self) -> Optional[HDNode]:
        return self._hd_path

    def hdAddressPath(
            self,
            account: int,
            is_change: bool,
            index: int) -> Optional[HDNode]:
        if self._hd_path is None:
            return None
        # FIXME broken path!
        address_path = self._hd_path.make_child_prv(
            index,
            False,
            self.network)
        return address_path

    def decodeAddress(self, **kwargs) -> Optional[Address]:
        return self.Address.decode(self, **kwargs)

    @property
    def addressList(self) -> List[Address]:
        return self._address_list

    def findAddressByName(self, name: str) -> Optional[Address]:
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for address in self._address_list:
            if name == address.name.casefold():
                return address
        return None

    def appendAddress(self, address: Address) -> bool:
        # TODO tmp, old wrapper
        if self.findAddressByName(address.name) is not None:  # noqa
            return False

        if self._model:
            self._model.beforeAppendAddress(address)
        self._address_list.append(address)
        if self._model:
            self._model.afterAppendAddress(address)

        self.refreshAmount()
        return True

    @property
    def serverData(self) -> dict:
        return self._server_data

    @serverData.setter
    def serverData(self, data: dict) -> None:
        self._server_data = data
        if self._model:
            self.model.afterSetServerData()

    def __createAddressListsForMempoolHelper(
            self,
            local_hash: Sha256Digest,
            address_list: List[str]) -> Dict[str, Any]:
        local_hash.update(b"\0")
        local_hash = local_hash.final()
        cache_value = self._mempool_cache.setdefault(
            local_hash, {
                "remote_hash": None,
                "access_count": 0
            })
        cache_value["access_count"] = self._mempool_cache_access_counter
        return {
            "local_hash": local_hash,
            "remote_hash": cache_value["remote_hash"],
            "list": address_list
        }

    def createMempoolAddressLists(
            self,
            count_per_list: int) -> List[Dict[str, Any]]:
        self._mempool_cache_access_counter += 1
        result = []

        address_list = []
        local_hash = Sha256Digest()

        for address in self.addressList:
            address_list.append(address.name)
            local_hash.update(address.name.encode("utf-8", "replace"))
            local_hash.update(b"\0")

            if len(address_list) >= count_per_list:
                result.append(self.__createAddressListsForMempoolHelper(
                    local_hash,
                    address_list))
                address_list = []
                local_hash = Sha256Digest()

        if len(address_list):
            result.append(self.__createAddressListsForMempoolHelper(
                local_hash,
                address_list))

        for key, cache_value in self._mempool_cache.copy().items():
            if cache_value["access_count"] < self._mempool_cache_access_counter:
                del self._mempool_cache[key]

        return result

    def setMempoolAddressListResult(
            self,
            local_hash: bytes,
            remote_hash: str) -> bool:
        cache_value = self._mempool_cache.get(local_hash)
        if cache_value is not None:
            cache_value["remote_hash"] = remote_hash
            return True
        return False

    @property
    def mutableTx(self) -> MutableTransaction:
        return self._mutable_tx
