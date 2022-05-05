from __future__ import annotations

import math
from contextlib import contextmanager
from typing import Final, Generator, TYPE_CHECKING
from weakref import WeakValueDictionary

from .object import CoinObject, CoinRootObjectModel
from ..hd import HdNode
from ...crypto.digest import Sha256Digest
from ...currency import Currency, FiatRate, NoneFiatCurrency
from ...database.tables import AddressesTable, CoinsTable
from ...utils import (
    DeserializeFlag,
    DeserializedData,
    SerializableList,
    serializable)
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from .object import CoinModelFactory, CoinObjectModel


class _Model(CoinRootObjectModel):
    def __init__(self, *args, coin: Coin, **kwargs) -> None:
        self._coin = coin
        super().__init__(*args, **kwargs)

    @property
    def owner(self) -> Coin:
        return self._coin

    def beforeSetIsEnabled(self, value: bool) -> None: pass
    def afterSetIsEnabled(self, value: bool) -> None: pass

    def beforeSetHeight(self, value: int) -> None: pass
    def afterSetHeight(self, value: int) -> None: pass

    def beforeSetVerifiedHeight(self, value: int) -> None: pass
    def afterSetVerifiedHeight(self, value: int) -> None: pass

    def beforeSetOffset(self, value: str) -> None: pass
    def afterSetOffset(self, value: str) -> None: pass

    def beforeSetUnverifiedOffset(self, value: int) -> None: pass
    def afterSetUnverifiedOffset(self, value: int) -> None: pass

    def beforeSetUnverifiedHash(self, value: int) -> None: pass
    def afterSetUnverifiedHash(self, value: int) -> None: pass

    def beforeSetOnlineStatus(self, value: int) -> None: pass
    def afterSetOnlineStatus(self, value: int) -> None: pass

    def beforeSetFiatRate(self, value: FiatRate) -> None: pass
    def afterSetFiatRate(self, value: FiatRate) -> None: pass

    def beforeUpdateBalance(self, value: int) -> None: pass
    def afterUpdateBalance(self, value: int) -> None: pass

    def beforeUpdateUtxoList(self, value: None) -> None: pass
    def afterUpdateUtxoList(self, value: None) -> None: pass

    def beforeAppendAddress(self, address: Coin.Address) -> None: pass
    def afterAppendAddress(self, address: Coin.Address) -> None: pass

    def beforeSetServerData(self, value: dict[str, ...]) -> None: pass
    def afterSetServerData(self, value: dict[str, ...]) -> None: pass


class Coin(CoinObject, table_type=CoinsTable):
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

    class MempoolCacheItem:
        __slots__ = ("remote_hash", "access_count")

        def __init__(
                self,
                *,
                remote_hash: str | None = None,
                access_count: int = 0) -> None:
            self.remote_hash = remote_hash
            self.access_count = access_count

    def __init__(
            self,
            *,
            model_factory: CoinModelFactory,
            **kwargs) -> None:
        super().__init__(self, kwargs)

        self._model_factory: Final = model_factory

        self._is_enabled = bool(kwargs.get("is_enabled", True))

        self._height = int(kwargs.get("height", 0))
        self._verified_height = int(kwargs.get("verified_height", 0))

        self._offset = str(kwargs.get("offset", ""))
        self._unverified_offset = str(kwargs.get("unverified_offset", ""))
        self._unverified_hash = str(kwargs.get("unverified_hash", ""))

        self._online_status: int = 0

        self._fiat_rate = FiatRate(0, NoneFiatCurrency)
        self._balance: int | None = None

        self._hd_node_list: dict[int, HdNode] = {}

        self._server_data: dict[str, int | str] = {}
        self._mempool_cache: dict[bytes, Coin.MempoolCacheItem] = {}
        self._mempool_cache_access_counter = 0
        self._tx_factory = self.TxFactory(self)

        self._appendDeferredSave(kwargs.pop("address_list", []))
        assert len(kwargs) == 0

    def __eq__(self, other: Coin) -> bool:
        return (
                super().__eq__(other)
                and self.name == other.name)

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self.name))

    # TODO cache
    def __str__(self) -> str:
        return StringUtils.classString(self.__class__, (None, self.name))

    def __update__(self, **kwargs) -> bool:
        self._appendDeferredSave(kwargs.pop("address_list", []))
        if not super().__update__(**kwargs):
            return False
        self.updateBalance()
        return True

    @classmethod
    def deserializeProperty(
            cls,
            flags: DeserializeFlag,
            self: Coin,
            key: str,
            value: DeserializedData,
            *cls_args) -> ...:
        if key == "address_list" and isinstance(value, dict):
            return lambda coin: coin.Address.deserialize(flags, value, coin)
        return super().deserializeProperty(flags, self, key, value, *cls_args)

    def modelFactory(self, owner: CoinObject) -> CoinObjectModel:
        return self._model_factory(owner)

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
        self._updateValue("set", "is_enabled", value)

    @serializable
    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._updateValue("set", "height", value)

    @serializable
    @property
    def verifiedHeight(self) -> int:
        return self._verified_height

    @verifiedHeight.setter
    def verifiedHeight(self, value: int) -> None:
        self._updateValue("set", "verified_height", value)

    @serializable
    @property
    def offset(self) -> str:
        return self._offset

    @offset.setter
    def offset(self, value: str) -> None:
        self._updateValue("set", "offset", value)

    @serializable
    @property
    def unverifiedOffset(self) -> str:
        return self._unverified_offset

    @unverifiedOffset.setter
    def unverifiedOffset(self, value: str) -> None:
        self._updateValue("set", "unverified_offset", value)

    @serializable
    @property
    def unverifiedHash(self) -> str:
        return self._unverified_hash

    @unverifiedHash.setter
    def unverifiedHash(self, value: str) -> None:
        self._updateValue("set", "unverified_hash", value)

    @property
    def onlineStatus(self) -> int:
        return self._online_status

    @onlineStatus.setter
    def onlineStatus(self, value: int) -> None:
        self._updateValue("set", "online_status", value)

    @property
    def fiatRate(self) -> FiatRate:
        return self._fiat_rate

    @fiatRate.setter
    def fiatRate(self, value: FiatRate) -> None:
        self._updateValue("set", "fiat_rate", value)

    def toFiatAmount(self, value: int | None = None) -> int | None:
        if value is None:
            if self._balance is None:
                return 0
            value = self._balance
        value *= self._fiat_rate.value
        value //= self.Currency.decimalDivisor
        if self._fiat_rate.currencyType.isValidValue(value):
            return value
        return None

    def fromFiatAmount(self, value: int) -> int | None:
        value *= self.Currency.decimalDivisor
        if self._fiat_rate.value:
            value = math.ceil(value / self._fiat_rate.value)
        else:
            value = 0
        return value if self.Currency.isValidValue(value) else None

    @property
    def balance(self) -> int:
        if self._balance is None:
            # Cannot query balance from __init__() (model not ready).
            # Therefore, try to run the query the first time this method is
            # called.
            if t := self._openTable(AddressesTable):
                self._balance = t.queryTotalBalance(self)
            else:
                self._balance = 0
        return self._balance

    def updateBalance(self) -> None:
        if t := self._openTable(AddressesTable):
            value = t.queryTotalBalance(self)
        else:
            value = 0
        self._updateValue("update", "balance", value)

    def updateUtxoList(self) -> None:
        self._updateValue(
            "update",
            "utxo_list",
            None,
            force=True,
            setattr_function=lambda *_: self._tx_factory.updateUtxoList())

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
    def hdNodeList(self) -> dict[int, HdNode]:
        return self._hd_node_list

    def nextHdIndex(self, purpose: int, account: int, change: int) -> int:
        parent_path = HdNode.pathJoin((
            HdNode.toHardenedLevel(purpose),
            HdNode.toHardenedLevel(self._BIP0044_COIN_TYPE),
            HdNode.toHardenedLevel(account),
            change))
        if t := self._openTable(AddressesTable):
            index = t.queryLastHdIndex(self, parent_path + HdNode.pathSeparator)
            return index + 1
        return -1

    def deriveHdAddress(
            self,
            *,
            account: int,
            is_change: bool,
            index: int = -1,
            type_: Address.Type | None = None,
            **kwargs) -> Address | None:
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
            if current_index < 0:
                return None
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
    def serverData(self) -> dict[str, ...]:
        return self._server_data

    @serverData.setter
    def serverData(self, value: dict[str, ...]) -> None:
        self._updateValue("set", "server_data", value)

    def __createAddressListsForMempoolHelper(
            self,
            local_hash: Sha256Digest,
            address_list: list[str]) -> dict[str, ...]:
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
            count_per_list: int) -> list[dict[str, ...]]:
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
