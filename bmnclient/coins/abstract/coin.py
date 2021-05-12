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
    from typing import Any, Callable, Dict, List, Optional, Tuple, Union
    from ...wallet.hd import HDNode


class AbstractCoin(Serializable):
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _IS_TEST_NET = False
    # https://github.com/satoshilabs/slips/blob/master/slip-0044.md
    _BIP0044_COIN_TYPE = -1

    class Interface:
        def __init__(self, *args, coin: AbstractCoin, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self._coin = coin

        def afterSetOffset(self) -> None:
            raise NotImplementedError

        def afterSetHeight(self) -> None:
            raise NotImplementedError

        def afterSetStatus(self) -> None:
            raise NotImplementedError

        def afterSetFiatRate(self) -> None:
            raise NotImplementedError

        def afterRefreshAmount(self) -> None:
            raise NotImplementedError

        def afterRefreshUtxoList(self) -> None:
            raise NotImplementedError

        def beforeAppendAddress(self, address: AbstractCoin.Address) -> None:
            raise NotImplementedError

        def afterAppendAddress(self, address: AbstractCoin.Address) -> None:
            raise NotImplementedError

        def afterSetServerData(self) -> None:
            raise NotImplementedError

        def afterStateChanged(self) -> None:
            raise NotImplementedError

    class Currency(AbstractCurrency):
        pass

    # noinspection PyAbstractClass
    class Address(AbstractAddress):
        pass

    class Tx(AbstractTx):
        pass

    class MutableTx(MutableTransaction):  # TODO AbstractMutableTx
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
        self.__old_state_hash = 0

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
        self._mutable_tx = self.MutableTx(self)

        self._model: Optional[AbstractCoin.Interface] = self.model_factory(self)

    def __eq__(self, other: AbstractCoin) -> bool:
        return (
                isinstance(other, self.__class__)
                and self.name == other.name
        )

    def __hash__(self) -> int:
        return hash((self.name, ))

    @classmethod
    def deserialize(cls, *args, **kwargs) -> Optional[AbstractCoin]:
        coin: AbstractCoin = args[0]
        return super().deserialize(
            *args,
            deserialize_create=coin._deserializeToSelf,
            **kwargs)

    @classmethod
    def _deserializeProperty(
            cls,
            args: Tuple[Any],
            key: str,
            value: Any) -> Any:
        if isinstance(value, dict) and key == "address_list":
            coin: AbstractCoin = args[0]
            return cls.Address.deserialize(coin, **value)
        return super()._deserializeProperty(args, key, value)

    def _deserializeToSelf(
            self,
            coin: AbstractCoin,
            *,
            name: str,
            height: int,
            verified_height: int,
            offset: str,
            unverified_offset: str,
            unverified_hash: str,
            address_list: Optional[List[Address]] = None) \
            -> Optional[AbstractCoin]:
        if self.name != name or id(coin) != id(self):
            return None

        self.beginUpdateState()
        if True:
            self.height = height
            self.verifiedHeight = verified_height
            self.offset = offset
            self.unverifiedOffset = unverified_offset
            self.unverifiedHash = unverified_hash

            if address_list is not None:
                self._address_list.clear()  # TODO clear with callback
                for address in address_list:
                    self.appendAddress(address)
        self.endUpdateState()
        return self

    @property
    def model(self) -> Optional[AbstractCoin.Interface]:
        return self._model

    def beginUpdateState(self) -> None:
        self.__old_state_hash = self.__state_hash

    def endUpdateState(self) -> bool:
        if self.__old_state_hash != self.__state_hash:
            self.__old_state_hash = self.__state_hash
            if self._model:
                self._model.afterStateChanged()
            return True
        return False

    def _updateState(self) -> int:
        old_value = self.__state_hash
        self.__state_hash = (old_value + 1) & ((1 << 64) - 1)
        return old_value

    def model_factory(self, owner: object) -> Optional[object]:
        if self._model_factory:
            return self._model_factory(owner)
        return None

    @serializable
    @property
    def name(cls) -> str:  # noqa
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
            self._offset = value
            self._updateState()
            if self._model:
                self._model.afterSetOffset()

    @serializable
    @property
    def unverifiedOffset(self) -> str:
        return self._unverified_offset

    @unverifiedOffset.setter
    def unverifiedOffset(self, value: str) -> None:
        if self._unverified_offset != value:
            self._unverified_offset = value
            self._updateState()

    @serializable
    @property
    def unverifiedHash(self) -> str:
        return self._unverified_hash

    @unverifiedHash.setter
    def unverifiedHash(self, value: str) -> None:
        if self._unverified_hash != value:
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
        if self._fiat_rate.currencyType.isValidValue(value):
            return value
        return None

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

    def refreshAmount(self) -> None:
        a = sum(a.amount for a in self._address_list if not a.isReadOnly)
        self._amount = a
        if self._model:
            self._model.afterRefreshAmount()

    def refreshUtxoList(self) -> None:
        self._mutable_tx.refreshSourceList()
        if self._model:
            self._model.afterRefreshUtxoList()

    def makeHdPath(self, purpose_path: HDNode) -> None:
        assert self._hd_path is None
        self._hd_path = purpose_path.make_child_prv(
            self._BIP0044_COIN_TYPE,
            True,
            self.network)

    @property
    def hdPath(self) -> Optional[HDNode]:
        return self._hd_path

    def nextHdIndex(self, account: int, is_change: bool) -> int:
        # FIXME broken path!
        index = 0
        for address in self._address_list:
            if address.hdIndex >= index:
                index = address.hdIndex + 1
        return index

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

    def createHdAddress(
            self,
            *,
            account: int,
            is_change: bool,
            index: int = -1,
            type_: Optional[Address.Type] = None,
            **kwargs) -> Optional[Address]:
        if self._hd_path is None:
            return None

        if type_ is None:
            type_ = self.Address.Type.DEFAULT

        if index < 0:
            # TODO fail if coin in "updating" mode
            index = self.nextHdIndex(account, is_change)
            assert index >= 0

        hd_path = self.hdAddressPath(account, is_change, index)
        if hd_path is None:
            return None

        address = self.Address(
            self,
            name=hd_path.to_address(type_.value.name),
            _type=type_,
            private_key=hd_path,
            **kwargs)
        return address

    @serializable
    @property
    def addressList(self) -> List[Address]:
        return self._address_list

    def findAddressByName(self, name: str) -> Optional[Address]:
        if not name:
            return None
        name = name.strip().casefold()  # TODO tmp, old wrapper
        for address in self._address_list:
            if name == address.name.casefold():
                return address
        return None

    def appendAddress(self, address: Address) -> bool:
        if address is None:
            return False
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
