from __future__ import annotations

import math
from typing import TYPE_CHECKING
from weakref import WeakValueDictionary

from .object import CoinObject, CoinObjectModel
from ..hd import HdNode
from ...crypto.digest import Sha256Digest
from ...currency import Currency, FiatRate, NoneFiatCurrency
from ...utils.class_property import classproperty
from ...utils.serialize import DeserializationNotSupportedError, serializable

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        Final,
        Generator,
        List,
        Optional,
        Union)
    from .object import CoinModelFactory
    from ...utils.serialize import DeserializedData


class _Model(CoinObjectModel):
    def __init__(self, *args, coin: Coin, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._coin = coin

    def afterSetEnabled(self) -> None:
        raise NotImplementedError

    def afterSetHeight(self) -> None:
        raise NotImplementedError

    def afterSetOffset(self) -> None:
        raise NotImplementedError

    def afterSetStatus(self) -> None:
        raise NotImplementedError

    def afterSetFiatRate(self) -> None:
        raise NotImplementedError

    def afterUpdateBalance(self) -> None:
        raise NotImplementedError

    def afterUpdateUtxoList(self) -> None:
        raise NotImplementedError

    def beforeAppendAddress(self, address: Coin.Address) -> None:
        raise NotImplementedError

    def afterAppendAddress(self, address: Coin.Address) -> None:
        raise NotImplementedError

    def afterSetServerData(self) -> None:
        raise NotImplementedError

    def afterStateChanged(self) -> None:
        raise NotImplementedError


class Coin(CoinObject):
    _SHORT_NAME = ""
    _FULL_NAME = ""
    _IS_TEST_NET = False

    # https://github.com/satoshilabs/slips/blob/master/slip-0044.md
    _BIP0044_COIN_TYPE = -1
    _BIP0032_VERSION_PUBLIC_KEY = -1
    _BIP0032_VERSION_PRIVATE_KEY = -1

    _WIF_VERSION = 0x00

    Model = _Model
    Currency = Currency

    from .address import _Address
    Address = _Address

    from .tx import _Tx
    Tx = _Tx

    from .tx_factory import _TxFactory
    TxFactory = _TxFactory

    from .script import _Script
    Script = _Script

    class MempoolCacheItem:
        __slots__ = ("remote_hash", "access_count")

        def __init__(
                self,
                *,
                remote_hash: Optional[str] = None,
                access_count: int = 0) -> None:
            self.remote_hash = remote_hash
            self.access_count = access_count

    def __init__(
            self,
            *,
            row_id: int = -1,
            model_factory: Optional[CoinModelFactory] = None) -> None:
        super().__init__(self, row_id=row_id)

        self._model_factory: Final = model_factory
        self.__state_hash = 0
        self.__old_state_hash = 0

        self._is_enabled = True

        self._height = 0
        self._verified_height = 0

        self._offset = ""
        self._unverified_offset = ""
        self._unverified_hash = ""

        self._status = 0

        self._fiat_rate = FiatRate(0, NoneFiatCurrency)
        self._balance = 0

        self._hd_node_list: Dict[int, HdNode] = {}

        self._address_list: List[Coin.Address] = []
        self._server_data: Dict[str, Union[int, str]] = {}
        self._mempool_cache: Dict[bytes, Coin.MempoolCacheItem] = {}
        self._mempool_cache_access_counter = 0
        self._tx_factory = self.TxFactory(self)

    def __eq__(self, other: Coin) -> bool:
        return (
                isinstance(other, self.__class__)
                and self.name == other.name
        )

    def __hash__(self) -> int:
        return hash((self.name, ))

    def __update__(self, **kwargs) -> bool:
        self.beginUpdateState()
        address_list = kwargs.pop("address_list", None)
        if address_list is not None:
            self._address_list.clear()  # TODO compare with new list!
            for address in address_list:
                self.appendAddress(address)
        result = super().__update__(**kwargs)
        self.endUpdateState()
        return result

    @classmethod
    def deserialize(cls, *_, **__) -> Optional[Coin]:
        raise DeserializationNotSupportedError

    @classmethod
    def _deserializeProperty(
            cls,
            self: Coin,
            key: str,
            value: DeserializedData,
            **options) -> Any:
        if isinstance(value, dict) and key == "address_list":
            return cls.Address.deserialize(value, self)
        return super()._deserializeProperty(self, key, value, **options)

    def beginUpdateState(self) -> None:
        self.__old_state_hash = self.__state_hash

    def endUpdateState(self) -> bool:
        if self.__old_state_hash != self.__state_hash:
            self.__old_state_hash = self.__state_hash
            self._callModel("afterStateChanged")
            return True
        return False

    def _updateState(self) -> int:
        old_value = self.__state_hash
        self.__state_hash = (old_value + 1) & ((1 << 64) - 1)
        return old_value

    def modelFactory(self, owner: CoinObject) -> Optional[CoinObjectModel]:
        return self._model_factory(owner) if self._model_factory else None

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
    def bip0044CoinType(cls) -> int:  # noqa
        return cls._BIP0044_COIN_TYPE

    @classproperty
    def bip0032VersionPublicKey(cls) -> int:  # noqa
        return cls._BIP0032_VERSION_PUBLIC_KEY

    @classproperty
    def bip0032VersionPrivateKey(cls) -> int:  # noqa
        return cls._BIP0032_VERSION_PRIVATE_KEY

    @classproperty
    def wifVersion(cls) -> int:  # noqa
        return cls._WIF_VERSION

    @classproperty
    def iconPath(cls) -> str:  # noqa
        # relative to "resources/images"
        return "coins/" + cls._SHORT_NAME + ".svg"

    @serializable
    @property
    def isEnabled(self) -> bool:
        return self._is_enabled

    @isEnabled.setter
    def isEnabled(self, value: bool):
        if self._is_enabled != value:
            self._is_enabled = value
            self._callModel("afterSetEnabled")

    @serializable
    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        if self._height != value:
            self._height = value
            self._updateState()
            self._callModel("afterSetHeight")

    @serializable
    @property
    def verifiedHeight(self) -> int:
        return self._verified_height

    @verifiedHeight.setter
    def verifiedHeight(self, value: int) -> None:
        if self._verified_height != value:
            self._verified_height = value
            self._updateState()

    @serializable
    @property
    def offset(self) -> str:
        return self._offset

    @offset.setter
    def offset(self, value: str) -> None:
        if self._offset != value:
            self._offset = value
            self._updateState()
            self._callModel("afterSetOffset")

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

    @property
    def status(self) -> int:
        return self._status

    @status.setter
    def status(self, value: int) -> None:
        if self._status != value:
            self._status = value
            self._callModel("afterSetStatus")

    @property
    def fiatRate(self) -> FiatRate:
        return self._fiat_rate

    @fiatRate.setter
    def fiatRate(self, fiat_rate: FiatRate) -> None:
        self._fiat_rate = fiat_rate
        self._callModel("afterSetFiatRate")

    def toFiatAmount(self, value: Optional[int] = None) -> Optional[int]:
        if value is None:
            value = self._balance
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
    def balance(self) -> int:
        return self._balance

    def updateBalance(self) -> None:
        a = sum(a.balance for a in self._address_list if not a.isReadOnly)
        self._balance = a
        self._callModel("afterUpdateBalance")

    def updateUtxoList(self) -> None:
        self._tx_factory.updateUtxoList()
        self._callModel("afterUpdateUtxoList")

    def deriveHdNode(self, root_node: HdNode) -> bool:
        private = root_node.privateKey is not None

        for type_ in self.Address.Type:
            purpose = type_.value.hdPurpose
            if purpose is None:
                continue
            hd_node = root_node.deriveChildNode(
                purpose,
                hardened=True,
                private=private)
            if hd_node is None:
                return False

            hd_node = hd_node.deriveChildNode(
                self._BIP0044_COIN_TYPE,
                hardened=True,
                private=private)
            if hd_node is None:
                return False

            self._hd_node_list[type_.value.hdPurpose] = hd_node

        return True

    @property
    def hdNodeList(self) -> Dict[int, HdNode]:
        return self._hd_node_list

    def nextHdIndex(self, purpose: int, account: int, change: int) -> int:
        index = 0
        parent_path = (
            HdNode.toHardenedLevel(purpose),
            HdNode.toHardenedLevel(self._BIP0044_COIN_TYPE),
            HdNode.toHardenedLevel(account),
            change)

        for address in self._address_list:
            if not isinstance(address.key, HdNode):
                continue
            if address.key.path[:-1] != parent_path:
                continue

            assert address.key.path[4] == address.key.index
            if address.key.index >= index:
                index = address.key.index + 1

        return index

    def deriveHdAddress(
            self,
            *,
            account: int,
            is_change: bool,
            index: int = -1,
            type_: Optional[Address.Type] = None,
            **kwargs) -> Optional[Address]:
        type_ = type_ if type_ is not None else self.Address.Type.DEFAULT
        if type_.value.hdPurpose is None:
            return None

        broken_mode = account == -1  # TODO remove in summer 2022

        if broken_mode:
            hd_node = self._hd_node_list.get(44)
        else:
            hd_node = self._hd_node_list.get(type_.value.hdPurpose)
        if hd_node is None:
            return None

        change = 1 if is_change else 0
        private = hd_node.privateKey is not None

        if index < 0:
            if broken_mode:
                return None
            # TODO should fail if coin in "updating" mode
            current_index = self.nextHdIndex(
                type_.value.hdPurpose,
                account,
                change)
        else:
            current_index = index

        if broken_mode:
            change_node = hd_node
        else:
            account_node = hd_node.deriveChildNode(
                account,
                hardened=True,
                private=private)
            if account_node is None:
                return None
            change_node = account_node.deriveChildNode(
                change,
                hardened=False,
                private=private)
            if change_node is None:
                return None

        while True:
            address_node = change_node.deriveChildNode(
                current_index,
                hardened=False,
                private=private)
            if address_node is not None:
                break
            if index >= 0:
                return None
            current_index += 1  # BIP-0032

        return self.Address.create(
            self,
            type_=type_,
            key=address_node,
            **kwargs)

    @serializable
    @property
    def addressList(self) -> List[Address]:
        return self._address_list

    def setTxInputAddress(self, address: Optional[Address]) -> None:
        # TODO
        if address is None:
            for a in self._address_list:
                a.isTxInput = False
        else:
            for a in self._address_list:
                if a == address:
                    a.isTxInput = True
                else:
                    a.isTxInput = False

    def filterAddressList(
            self,
            *,
            is_read_only: Optional[bool] = None,
            is_tx_input: Optional[bool] = None,
            with_utxo: Optional[bool] = None) -> Generator[Address, None, None]:
        # TODO temporary
        tx_input_found = False
        if is_tx_input:
            for address in self._address_list:
                if address.isTxInput:
                    tx_input_found = True

        for address in self._address_list:
            if is_read_only is not None:
                if is_read_only != address.isReadOnly:
                    continue
            if tx_input_found and is_tx_input is not None:
                if is_tx_input != address.isTxInput:
                    continue
            if with_utxo is not None:
                if (len(address.utxoList) > 0) != with_utxo:
                    continue
            yield address

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

        self._callModel("beforeAppendAddress", address)
        self._address_list.append(address)
        self._callModel("afterAppendAddress", address)

        self.updateBalance()
        return True

    @property
    def serverData(self) -> dict:
        return self._server_data

    @serverData.setter
    def serverData(self, data: dict) -> None:
        self._server_data = data
        self._callModel("afterSetServerData")

    def __createAddressListsForMempoolHelper(
            self,
            local_hash: Sha256Digest,
            address_list: List[str]) -> Dict[str, Any]:
        local_hash = local_hash.update(b"\0").finalize()
        cache_value = self._mempool_cache.setdefault(
            local_hash,
            self.MempoolCacheItem())
        cache_value.access_count = self._mempool_cache_access_counter
        return {
            "local_hash": local_hash,
            "remote_hash": cache_value.remote_hash,
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
            if cache_value.access_count < self._mempool_cache_access_counter:
                del self._mempool_cache[key]

        return result

    def setMempoolAddressListResult(
            self,
            local_hash: bytes,
            remote_hash: str) -> bool:
        cache_value = self._mempool_cache.get(local_hash)
        if cache_value is not None:
            cache_value.remote_hash = remote_hash
            return True
        return False

    @property
    def txFactory(self) -> TxFactory:
        return self._tx_factory

    def weakValueDictionary(self, name: str):
        heap = self.__dict__.get(name)
        if heap is None:
            heap = WeakValueDictionary()
            self.__dict__[name] = heap
        return heap
