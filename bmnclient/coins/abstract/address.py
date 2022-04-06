from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from .object import CoinObject, CoinObjectModel
from ..hd import HdNode
from ..utils import CoinUtils
from ...crypto.secp256k1 import PrivateKey, PublicKey
from ...database.tables import AddressTxsTable, AddressesTable, UtxosTable
from ...utils import SerializeFlag, serializable
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Any, Final, List, Optional, Union
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
            encoding: Optional[Coin.Address.Encoding],
            is_witness: bool,
            script_type: Optional[Coin.Address.Script.Type],
            hd_purpose: Optional[int]) -> None:
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
    def encoding(self) -> Optional[Coin.Address.Encoding]:
        return self._encoding

    @property
    def isWitness(self) -> bool:
        return self._is_witness

    @property
    def scriptType(self) -> Optional[Coin.Address.Script.Type]:
        return self._script_type

    @property
    def hdPurpose(self) -> Optional[int]:
        return self._hd_purpose


class _Model(CoinObjectModel):
    def __init__(self, *args, address: Coin.Address, **kwargs) -> None:
        super().__init__(
            *args,
            name_key_tuple=CoinUtils.addressToNameKeyTuple(address),
            **kwargs)
        self._address = address

    @property
    def owner(self) -> Coin.Address:
        return self._address

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

    def beforeSetTxCount(self, value: int) -> None: pass
    def afterSetTxCount(self, value: int) -> None: pass
    def beforeAppendTx(self, tx: Coin.Tx) -> None: pass
    def afterAppendTx(self, tx: Coin.Tx) -> None: pass
    def afterSetUtxoList(self) -> None: pass  # TODO
    def afterSetUtxoList(self) -> None: pass

    def beforeSetHistoryFirstOffset(self, value: str) -> None: pass
    def afterSetHistoryFirstOffset(self, value: str) -> None: pass

    def beforeSetHistoryLastOffset(self, value: str) -> None: pass
    def afterSetHistoryLastOffset(self, value: str) -> None: pass


class _Address(CoinObject, table_type=AddressListTable):
    __initialized = False

    _NULLDATA_NAME = "NULL_DATA"
    _HRP = "hrp"

    if TYPE_CHECKING:
        KeyType = Union[HdNode, PrivateKey, PublicKey]

    class Encoding(Enum):
        BASE58 = auto()
        BECH32 = auto()

    Model = _Model

    from .script import _Script
    Script = _Script

    TypeValue = _TypeValue
    Type = Enum

    def __new__(cls, coin: Coin, *args, **kwargs) -> _Address:
        # noinspection PyUnresolvedReferences
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

        super().__init__(coin, row_id=row_id)

        self.__hash: Optional[bytes] = None

        self._name: Final[str] = kwargs.get("name") or self._NULLDATA_NAME
        self._type: Final[_Address.Type] = kwargs["type_"]
        self._data: Final[bytes] = kwargs.get("data", b"")
        self._key: Optional[_Address.KeyType] = kwargs.get("key", None)
        self._balance: int = kwargs.get("balance", 0)
        self._label: str = kwargs.get("label", "")
        self._comment: str = kwargs.get("comment", "")
        self._is_tx_input = bool(kwargs.get("is_tx_input", False))

        self._tx_count: int = kwargs.get("tx_count", 0)
        self._tx_list: List[Coin.Tx] = list(kwargs.get("tx_list", []))
        self._utxo_list: List[Coin.Tx.Utxo] = list(kwargs.get("utxo_list", []))

        history_first_offset: str = kwargs.get("history_first_offset", "")
        history_last_offset: str = kwargs.get("history_last_offset", "")
        if history_first_offset and history_last_offset:
            self._history_first_offset = history_first_offset
            self._history_last_offset = history_last_offset
        else:
            self._history_first_offset = ""
            self._history_last_offset = ""

    def __eq__(self, other: _Address) -> bool:
        return (
                super().__eq__(other)
                and self._name == other.name
                and self._type == other._type
        )

    def __hash__(self) -> int:
        return hash((
            super().__hash__(),
            self._name,
            self._type
        ))

    def serializeProperty(
            self,
            flags: SerializeFlag,
            key: str,
            value: Any) -> DeserializedData:
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
            self: Optional[_Address],
            key: str,
            value: DeserializedData,
            *cls_args) -> Any:
        coin = cls_args[0] if cls_args else self._coin
        if key == "type":
            for t in cls.Type:
                if value == t.value.name:
                    return t
            # noinspection PyUnresolvedReferences
            return cls.Type.UNKNOWN
        if isinstance(value, str) and key == "key":
            return cls.importKey(coin, value)
        if key == "tx_list":
            if isinstance(value, dict):
                return coin.Tx.deserialize(flags, value, coin)
            elif isinstance(value, coin.Tx):
                return value
        if key == "utxo_list":
            if isinstance(value, dict):
                return coin.Tx.Utxo.deserialize(flags, value, coin)
            elif isinstance(value, coin.Tx.Utxo):
                return value
        return super()._deserializeProperty(flags, self, key, value, *cls_args)

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

    @classmethod
    def create(
            cls,
            coin: Coin,
            *,
            type_: _Address.Type,
            key: KeyType,
            **kwargs) -> Optional[_Address]:
        return cls(coin, type_=type_, key=key, **kwargs)

    @classmethod
    def createFromName(
            cls,
            coin: Coin,
            *,
            name: str,
            **kwargs) -> Optional[_Address]:
        return cls(coin, name=name, **kwargs)

    @classmethod
    def createNullData(
            cls,
            coin: Coin,
            *,
            name: Optional[str] = None,
            **kwargs) -> _Address:
        # noinspection PyUnresolvedReferences
        return cls(coin, name=name, type_=cls.Type.UNKNOWN, **kwargs)

    @property
    def isNullData(self) -> bool:
        # noinspection PyUnresolvedReferences
        return self._type == self.Type.UNKNOWN

    @property
    def data(self) -> bytes:
        return self._data

    @classmethod
    def _publicKey(cls, key: Optional[KeyType]) -> Optional[PublicKey]:
        if isinstance(key, HdNode):
            return key.publicKey
        if isinstance(key, PrivateKey):
            return key.publicKey
        if isinstance(key, PublicKey):
            return key
        return None

    @property
    def publicKey(self) -> Optional[PublicKey]:
        return self._publicKey(self._key)

    @property
    def privateKey(self) -> Optional[PrivateKey]:
        if isinstance(self._key, HdNode):
            value = self._key.privateKey
        elif isinstance(self._key, PrivateKey):
            value = self._key
        else:
            value = None
        return value

    @serializable
    @property
    def key(self) -> Optional[KeyType]:
        return self._key

    @key.setter
    def key(self, value: Optional[KeyType]) -> None:
        self._updateValue("set", "key", value)

    def exportKey(self, *, allow_hd_path: bool = False) -> Optional[str]:
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
    def importKey(cls, coin: Coin, value: str) -> Optional[KeyType]:
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

    @serializable
    @property
    def isTxInput(self) -> bool:
        return self._is_tx_input

    @isTxInput.setter
    def isTxInput(self, value: bool) -> None:
        self._updateValue("set", "is_tx_input", value)

    @property
    def isReadOnly(self) -> bool:
        return self.privateKey is None

    @serializable
    @property
    def txCount(self) -> int:
        return self._tx_count

    @txCount.setter
    def txCount(self, value: int) -> None:
        self._updateValue("set", "tx_count", value)

    @serializable
    @property
    def txList(self) -> List[Coin.Tx]:
        return self._tx_list

    def appendTx(self, tx: Coin.Tx) -> bool:
        for etx in self._tx_list:
            if tx.name != etx.name:
                continue
            if etx.height == -1:
                etx.height = tx.height
                etx.time = tx.time
                # TODO compare/replace input/output list
                return True
            return False

        self._callModel("beforeAppendTx", tx)
        self._tx_list.append(tx)
        self._callModel("afterAppendTx", tx)
        return True

    @serializable
    @property
    def utxoList(self) -> Sequence[Coin.Tx.Utxo]:
        if self._isTableAvailable:
            result = self.model.database[UtxoListTable].rowListProxy(self)
            if result is not None:
                return result
        return tuple()

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
        with self.model.database.transaction(allow_in_transaction=True):
            if self._updateValue("set", "history_first_offset", value):
                if not value:
                    self.historyLastOffset = ""

    @serializable
    @property
    def historyLastOffset(self) -> str:
        return self._history_last_offset

    @historyLastOffset.setter
    def historyLastOffset(self, value: str):
        with self.model.database.transaction(allow_in_transaction=True):
            if self._updateValue("set", "history_last_offset", value):
                if not value:
                    self.historyFirstOffset = ""
