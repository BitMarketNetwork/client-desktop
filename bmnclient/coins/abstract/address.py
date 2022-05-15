from __future__ import annotations

from enum import Enum, auto
from typing import Final, Sequence, TYPE_CHECKING, Union

from .object import CoinObject, CoinObjectModel
from ..hd import HdNode
from ...crypto.secp256k1 import PrivateKey, PublicKey
from ...database.tables import AddressTxsTable, AddressesTable, UtxosTable
from ...utils import SerializableList, SerializeFlag, serializable
from ...utils.class_property import classproperty
from ...utils.string import StringUtils

if TYPE_CHECKING:
    from .coin import Coin
    from ...utils import DeserializeFlag, DeserializedData


class _TypeValue:
    __slots__ = (
        "_name",
        "_version",
        "_size",
        "_encoding",
        "_is_witness",
        "_script_type",
        "_hd_purpose"
    )

    def __init__(
            self,
            *,
            name: str,
            version: int,
            size: int,
            encoding: Coin.Address.Encoding | None,
            is_witness: bool,
            script_type: Coin.Address.Script.Type,
            hd_purpose: int | None) -> None:
        self._name: Final = name
        self._version: Final = version
        self._size: Final = size
        self._encoding: Final = encoding
        self._is_witness: Final = is_witness
        self._script_type: Final = script_type
        self._hd_purpose: Final = hd_purpose

    def __eq__(self, other: _TypeValue) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._name == other._name
                and self._version == other._version
                and self._size == other._size
                and self._encoding == other._encoding
                and self._script_type == other._script_type
                and self._hd_purpose == other._hd_purpose
        )

    def __hash__(self) -> int:
        return hash((
            self._name,
            self._version,
            self._size,
            self._encoding,
            self._script_type,
            self._hd_purpose))

    def copy(self, **kwargs) -> _TypeValue:
        return self.__class__(
            name=kwargs.get("name", self._name),
            version=kwargs.get("version", self._version),
            size=kwargs.get("size", self._size),
            encoding=kwargs.get("encoding", self._encoding),
            is_witness=kwargs.get("is_witness", self._is_witness),
            script_type=kwargs.get("script_type", self._script_type),
            hd_purpose=kwargs.get("hd_purpose", self._hd_purpose),
        )

    def isValidSize(self, size: int) -> bool:
        if self._size > 0:
            if self._size == size:
                return True
        elif self._size < 0:
            if 0 < size <= abs(self._size):
                return True
        return False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> int:
        return self._version

    @property
    def size(self) -> int:
        return self._size

    @property
    def encoding(self) -> Coin.Address.Encoding | None:
        return self._encoding

    @property
    def isWitness(self) -> bool:
        return self._is_witness

    @property
    def scriptType(self) -> Coin.Address.Script.Type:
        return self._script_type

    @property
    def hdPurpose(self) -> int | None:
        return self._hd_purpose


class _Model(CoinObjectModel):
    def __init__(self, *args, address: Coin.Address, **kwargs) -> None:
        self._address = address
        super().__init__(*args, **kwargs)

    @property
    def owner(self) -> Coin.Address:
        return self._address

    def afterInsertSelf(self) -> None:
        self._address.coin.updateBalance()
        self._address.coin.model.queryScheduler.updateCoinAddress(self._address)
        super().afterInsertSelf()

    def beforeSetKey(self, value: Coin.Address.KeyType) -> None: pass
    def afterSetKey(self, value: Coin.Address.KeyType) -> None: pass

    def beforeSetBalance(self, value: int) -> None: pass
    def afterSetBalance(self, value: int) -> None: pass

    def beforeSetLabel(self, value: str) -> None: pass
    def afterSetLabel(self, value: str) -> None: pass

    def beforeSetComment(self, value: str) -> None: pass
    def afterSetComment(self, value: str) -> None: pass

    def beforeSetIsTxInput(self, value: bool) -> None: pass
    def afterSetIsTxInput(self, value: bool) -> None: pass

    def beforeSetIsReadOnly(self, value: bool) -> None: pass
    def afterSetIsReadOnly(self, value: bool) -> None: pass

    def beforeSetTxCount(self, value: int) -> None: pass
    def afterSetTxCount(self, value: int) -> None: pass

    def beforeSetHistoryFirstOffset(self, value: str) -> None: pass
    def afterSetHistoryFirstOffset(self, value: str) -> None: pass

    def beforeSetHistoryLastOffset(self, value: str) -> None: pass
    def afterSetHistoryLastOffset(self, value: str) -> None: pass


class _Address(
        CoinObject,
        table_type=AddressesTable,
        associated_table_type=AddressTxsTable):
    __initialized = False

    _NULLDATA_NAME = "NULL_DATA"
    _HRP = "hrp"

    class Encoding(Enum):
        BASE58 = auto()
        BECH32 = auto()

    Model = _Model

    from .script import _Script
    Script = _Script

    TypeValue = _TypeValue
    Type = Enum
    KeyType = Union[HdNode, PrivateKey, PublicKey]

    def __new__(cls, coin: Coin, *args, **kwargs) -> _Address:
        if kwargs.get("type_") == cls.Type.UNKNOWN or not kwargs.get("name"):
            return super().__new__(cls)

        heap = coin.weakValueDictionary("address_heap")
        address = heap.get(kwargs["name"])
        if address is None:
            address = super().__new__(cls)
        heap[kwargs["name"]] = address
        return address

    def __init__(self, coin: Coin, **kwargs) -> None:
        if self.__initialized:
            assert self._coin is coin
            self.__update__(**kwargs)
            return
        self.__initialized = True

        self._name: Final = str(kwargs.get("name") or self._NULLDATA_NAME)
        self._type: Final[_Address.Type] = kwargs["type_"]
        assert isinstance(self._type, self.Type)

        super().__init__(
            coin,
            kwargs,
            enable_table=(self._name and self._type != self.Type.UNKNOWN))

        self.__hash: bytes | None = None
        self._balance = int(kwargs.pop("balance", 0))
        self._tx_count = int(kwargs.pop("tx_count", 0))
        self._label = str(kwargs.pop("label", ""))
        self._comment = str(kwargs.pop("comment", ""))

        self._is_tx_input = bool(kwargs.pop("is_tx_input", False))
        self._data: Final = bytes(kwargs.pop("data", b""))
        self._key: _Address.KeyType | None = kwargs.pop("key", None)
        assert self._key is None or isinstance(self._key, self.KeyType)
        self._is_read_only = bool(kwargs.pop(
            "is_read_only",
            self.privateKey is None))

        history_first_offset = str(kwargs.pop("history_first_offset", ""))
        history_last_offset = str(kwargs.pop("history_last_offset", ""))
        if history_first_offset and history_last_offset:
            self._history_first_offset = history_first_offset
            self._history_last_offset = history_last_offset
        else:
            self._history_first_offset = ""
            self._history_last_offset = ""

        self._appendDeferredSave(
            lambda: self.txList,
            kwargs.pop("tx_list", []))
        self._appendDeferredSave(
            lambda: self.utxoList,
            kwargs.pop("utxo_list", []))
        assert len(kwargs) == 2

    def __eq__(self, other: _Address) -> bool:
        return (
                super().__eq__(other)
                and self._name == other.name
                and self._type == other._type)

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._name,
            self._type))

    # TODO cache
    def __str__(self) -> str:
        return StringUtils.classString(
            self.__class__,
            (None, self._name),
            (
                "path",
                self._key.pathToString()
                if isinstance(self._key, HdNode)
                else ""
            ),
            parent=self.coin)

    def __update__(self, **kwargs) -> bool:
        self._appendDeferredSave(
            lambda: self.txList,
            kwargs.pop("tx_list", []))
        self._appendDeferredSave(
            lambda: self.utxoList,
            kwargs.pop("utxo_list", []))
        if not super().__update__(**kwargs):
            return False
        # TODO self.updateBalance()
        return True

    @classmethod
    def create(
            cls,
            coin: Coin,
            *,
            type_: _Address.Type,
            key: KeyType,
            **kwargs) -> _Address | None:
        return cls(coin, type_=type_, key=key, **kwargs)

    @classmethod
    def createFromName(
            cls,
            coin: Coin,
            *,
            name: str,
            **kwargs) -> _Address | None:
        return cls(coin, name=name, **kwargs)

    @classmethod
    def createNullData(
            cls,
            coin: Coin,
            *,
            name: str | None = None,
            **kwargs) -> _Address | None:
        return cls(coin, name=name, type_=cls.Type.UNKNOWN, **kwargs)

    def serializeProperty(
            self,
            flags: SerializeFlag,
            key: str,
            value: ...) -> DeserializedData:
        if key == "key":
            # TODO temporary, unsecure
            if bool(flags & SerializeFlag.PUBLIC_MODE):
                return self.exportKey(allow_hd_path=True)
            elif bool(flags & SerializeFlag.PRIVATE_MODE):
                return self.exportKey(allow_hd_path=False)
            elif bool(flags & SerializeFlag.DATABASE_MODE):
                return self.exportKey(allow_hd_path=True)
            else:
                return ""
        if key == "type":
            return value.value.name
        return super().serializeProperty(flags, key, value)

    @classmethod
    def deserializeProperty(
            cls,
            flags: DeserializeFlag,
            self: _Address | None,
            key: str,
            value: DeserializedData,
            *cls_args) -> ...:
        if key == "type":
            for t in cls.Type:
                if value == t.value.name:
                    return t
            return cls.Type.UNKNOWN
        if isinstance(value, str) and key == "key":
            address = cls_args[0] if cls_args else self
            return cls.importKey(address._coin, value)
        if key == "tx_list" and isinstance(value, dict):
            return lambda a: a.coin.Tx.deserialize(flags, value, a.coin)
        if key == "utxo_list" and isinstance(value, dict):
            return lambda a: a.coin.Tx.Utxo.deserialize(flags, value, a)
        return super().deserializeProperty(flags, self, key, value, *cls_args)

    @classproperty
    def hrp(cls) -> str:  # noqa
        return cls._HRP

    @serializable
    @property
    def name(self) -> str:
        return self._name

    @property
    def hash(self) -> bytes:
        if self.__hash is None:
            self.__hash = self._deriveHash()
        return self.__hash

    def _deriveHash(self) -> bytes:
        raise NotImplementedError

    @serializable
    @property
    def type(self) -> _Address.Type:
        return self._type

    @property
    def isNullData(self) -> bool:
        # noinspection PyUnresolvedReferences
        return self._type == self.Type.UNKNOWN

    @property
    def data(self) -> bytes:
        return self._data

    @classmethod
    def _publicKey(cls, key: KeyType | None) -> PublicKey | None:
        if isinstance(key, HdNode):
            return key.publicKey
        if isinstance(key, PrivateKey):
            return key.publicKey
        if isinstance(key, PublicKey):
            return key
        return None

    @property
    def publicKey(self) -> PublicKey | None:
        return self._publicKey(self._key)

    @property
    def privateKey(self) -> PrivateKey | None:
        if isinstance(self._key, HdNode):
            value = self._key.privateKey
        elif isinstance(self._key, PrivateKey):
            value = self._key
        else:
            value = None
        return value

    @serializable
    @property
    def key(self) -> KeyType | None:
        return self._key

    @key.setter
    def key(self, value: KeyType | None) -> None:
        self._updateValue("set", "key", value)
        if self.privateKey is None:
            self._updateValue("set", "is_read_only", True)

    def exportKey(self, *, allow_hd_path: bool = False) -> str | None:
        if isinstance(self._key, HdNode):
            if allow_hd_path and self._key.isFullPath:
                value = self._key.pathToString()
            else:
                value = None

            if value is None:
                value = self._key.toExtendedKey(
                    self._coin.bip0032VersionPrivateKey,
                    private=True)

            if value is None:
                value = self._key.toExtendedKey(
                    self._coin.bip0032VersionPublicKey,
                    private=False)
        elif isinstance(self._key, PrivateKey):
            value = self._key.toWif(self._coin.wifVersion)
        elif isinstance(self._key, PublicKey):
            value = self._key.data.hex()
        else:
            value = None

        return value

    @classmethod
    def importKey(cls, coin: Coin, value: str) -> KeyType | None:
        if not value:
            return None

        hd_path, is_full_hd_path = HdNode.pathFromString(value)
        if hd_path is not None:
            if is_full_hd_path and len(hd_path):
                for coin_hd_node in coin.hdNodeList.values():
                    if len(hd_path) <= len(coin_hd_node.path):
                        continue
                    if hd_path[:len(coin_hd_node.path)] != coin_hd_node.path:
                        continue
                    key = coin_hd_node.fromPath(
                        hd_path[len(coin_hd_node.path):],
                        private=coin_hd_node.privateKey is not None)
                    return key
            return None

        version, key = HdNode.fromExtendedKey(value)
        if key is not None:
            if key.privateKey is not None:
                if version == coin.bip0032VersionPrivateKey:
                    return key
            else:
                if version == coin.bip0032VersionPublicKey:
                    return key
            return None

        version, key = PrivateKey.fromWif(value)
        if key is not None:
            if version == coin.wifVersion:
                return key
            return None

        try:
            value = bytes.fromhex(value)
        except (TypeError, ValueError):
            return None

        key = PrivateKey.fromSecretData(value, is_compressed=True)
        if key is not None:
            return key

        return PublicKey.fromPublicData(value)

    @serializable
    @property
    def balance(self) -> int:
        return self._balance

    @balance.setter
    def balance(self, value: int) -> None:
        self._updateValue("set", "balance", value)
        self._coin.updateBalance()

    @serializable
    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._updateValue("set", "label", value)

    @serializable
    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        self._updateValue("set", "comment", value)

    @serializable  # TODO column
    @property
    def isTxInput(self) -> bool:
        return self._is_tx_input

    @isTxInput.setter
    def isTxInput(self, value: bool) -> None:
        self._updateValue("set", "is_tx_input", value)

    @serializable
    @property
    def isReadOnly(self) -> bool:
        return bool(self._is_read_only or self.privateKey is None)

    @isReadOnly.setter
    def isReadOnly(self, value: bool) -> None:
        value = bool(value or self.privateKey is None)
        self._updateValue("set", "is_read_only", value)

    @serializable
    @property
    def txCount(self) -> int:
        return self._tx_count

    @txCount.setter
    def txCount(self, value: int) -> None:
        self._updateValue("set", "tx_count", value)

    @serializable
    @property
    def txList(self) -> SerializableList[Coin.Tx]:
        return self._rowList(AddressTxsTable)

    @serializable
    @property
    def utxoList(self) -> SerializableList[Coin.Tx.Utxo]:
        return self._rowList(UtxosTable)

    @utxoList.setter
    def utxoList(self, utxo_list: List[Coin.Tx.Utxo]) -> None:
        if self._utxo_list == utxo_list:
            return

        for utxo in utxo_list:
            utxo.address = self
        self._utxo_list = utxo_list

        self._callModel("afterSetUtxoList")
        self._coin.updateUtxoList()

        self.balance = sum(u.amount for u in self._utxo_list)

    @serializable
    @property
    def historyFirstOffset(self) -> str:
        return self._history_first_offset

    @historyFirstOffset.setter
    def historyFirstOffset(self, value: str):
        def clear() -> None:
            self.historyLastOffset = ""
        self._updateValue(
            "set",
            "history_first_offset",
            value,
            on_update=None if value else clear)

    @serializable
    @property
    def historyLastOffset(self) -> str:
        return self._history_last_offset

    @historyLastOffset.setter
    def historyLastOffset(self, value: str):
        def clear() -> None:
            self.historyFirstOffset = ""
        self._updateValue(
            "set",
            "history_last_offset",
            value,
            on_update=None if value else clear)
