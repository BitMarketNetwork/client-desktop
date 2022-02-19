from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from .serialize import _CoinSerializable
from ..hd import HdNode
from ...crypto.secp256k1 import PrivateKey, PublicKey
from ...debug import Debug
from ...utils.class_property import classproperty
from ...utils.serialize import serializable

if TYPE_CHECKING:
    from typing import Any, Iterable, List, Optional, Union
    from .coin import Coin
    from ...utils.serialize import DeserializedData, DeserializedDict


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
            script_type: Optional[Coin.Script.Type],
            hd_purpose: Optional[int]) -> None:
        self._name = name
        self._version = version
        self._size = size
        self._encoding = encoding
        self._is_witness = is_witness
        self._script_type = script_type
        self._hd_purpose = hd_purpose

    def __eq__(self, other: Coin.Address.TypeValue) -> bool:
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

    def copy(self, **kwargs) -> Coin.Address.TypeValue:
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
    def scriptType(self) -> Optional[Coin.Script.Type]:
        return self._script_type

    @property
    def hdPurpose(self) -> Optional[int]:
        return self._hd_purpose


class _Interface:
    def __init__(
            self,
            *args,
            address: Coin.Address,
            **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._address = address

    def afterSetBalance(self) -> None:
        raise NotImplementedError

    def afterSetLabel(self) -> None:
        raise NotImplementedError

    def afterSetComment(self) -> None:
        raise NotImplementedError

    def afterSetIsTxInput(self) -> None:
        raise NotImplementedError

    def afterSetTxCount(self) -> None:
        raise NotImplementedError

    def beforeAppendTx(self, tx: Coin.Tx) -> None:
        raise NotImplementedError

    def afterAppendTx(self, tx: Coin.Tx) -> None:
        raise NotImplementedError

    def afterSetUtxoList(self) -> None:
        raise NotImplementedError

    def afterSetHistoryFirstOffset(self) -> None:
        raise NotImplementedError

    def afterSetHistoryLastOffset(self) -> None:
        raise NotImplementedError


class _Address(_CoinSerializable):
    _NULLDATA_NAME = "NULL_DATA"
    _HRP = "hrp"

    if TYPE_CHECKING:
        KeyType = Union[HdNode, PrivateKey, PublicKey]

    class Encoding(Enum):
        BASE58 = auto()
        BECH32 = auto()

    Interface = _Interface
    TypeValue = _TypeValue
    Type = Enum

    def __init__(
            self,
            coin: Coin,
            *,
            row_id: int = -1,
            name: Optional[str],
            type_: Coin.Address.Type,
            data: bytes = b"",
            key: Optional[KeyType] = None,
            balance: int = 0,
            tx_count: int = 0,
            label: str = "",
            comment: str = "",
            is_tx_input: bool = False,
            tx_list: Optional[Iterable[Coin.Tx]] = None,
            utxo_list: Optional[Iterable[Coin.Tx.Utxo]] = None,
            history_first_offset: str = "",
            history_last_offset: str = "") -> None:
        #Debug.assertObjectCaller(coin, "_allocateAddress")
        super().__init__(row_id=row_id)

        self._coin = coin
        self._name = name or self._NULLDATA_NAME
        self.__hash: Optional[bytes] = None
        self._type = type_
        self._data = data
        self._key = key
        self._balance = balance
        self._label = label
        self._comment = comment
        self._is_tx_input = bool(is_tx_input)
        self._tx_count = tx_count  # not linked with self._tx_list

        self._tx_list = (
            [] if tx_list is None else list(tx_list)
        )
        self._utxo_list = (
            [] if tx_list is None else list(utxo_list)
        )

        if history_first_offset and history_last_offset:
            self._history_first_offset = history_first_offset
            self._history_last_offset = history_last_offset
        else:
            self._history_first_offset = ""
            self._history_last_offset = ""

        self._model: Optional[Coin.Address.Interface] = \
            self._coin.model_factory(self)

    def __eq__(self, other: Coin.Address) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._coin == other.coin
                and self._name == other.name
                and self._type == other._type
        )

    def __hash__(self) -> int:
        return hash((
            self.coin,
            self._name,
            self._type
        ))

    def serialize(
            self,
            *,
            allow_hd_path: bool = True,
            **options) -> DeserializedDict:
        return super().serialize(allow_hd_path=allow_hd_path, **options)

    def _serializeProperty(
            self,
            key: str,
            value: Any,
            **options) -> DeserializedData:
        if key == "key":
            return self.exportKey(allow_hd_path=options["allow_hd_path"])
        return super()._serializeProperty(key, value, **options)

    @classmethod
    def _deserializeProperty(
            cls,
            key: str,
            value: DeserializedData,
            coin: Optional[Coin] = None,
            **options) -> Any:
        if isinstance(value, str) and key == "key":
            return cls.importKey(coin, value)
        if key == "tx_list":
            if isinstance(value, dict):
                return coin.Tx.deserialize(value, coin)
            elif isinstance(value, coin.Tx):
                return value
        if key == "utxo_list":
            if isinstance(value, dict):
                return coin.Tx.Utxo.deserialize(value, coin)
            elif isinstance(value, coin.Tx.Utxo):
                return value
        return super()._deserializeProperty(key, value, coin, **options)

    @classmethod
    def _deserializeFactory(
            cls,
            coin: Coin,
            **kwargs) -> Optional[Coin.Address]:
        return cls.createFromName(coin, **kwargs)

    @classproperty
    def hrp(cls) -> str:  # noqa
        return cls._HRP

    @property
    def model(self) -> Optional[Coin.Address.Interface]:
        return self._model

    @property
    def coin(self) -> Coin:
        return self._coin

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

    @property
    def type(self) -> Coin.Address.Type:
        return self._type

    @classmethod
    def create(
            cls,
            coin: Coin,
            *,
            type_: Coin.Address.Type,
            key: KeyType,
            **kwargs) -> Optional[Coin.Address]:
        raise NotImplementedError

    @classmethod
    def createFromName(
            cls,
            coin: Coin,
            *,
            name: str,
            **kwargs) -> Optional[Coin.Address]:
        raise NotImplementedError

    @classmethod
    def createNullData(
            cls,
            coin: Coin,
            *,
            name: Optional[str] = None,
            **kwargs) -> Coin.Address:
        raise NotImplementedError

    @classmethod
    def _create(
            cls,
            coin: Coin,
            *,
            is_null_data: bool,
            name: Optional[str],
            **kwargs) -> Optional[Coin.Address]:
        # noinspection PyProtectedMember
        return coin._allocateAddress(
            is_null_data=is_null_data,
            name=name,
            **kwargs)

    @property
    def isNullData(self) -> bool:
        raise NotImplementedError

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
        if self._balance != value:
            self._balance = value
            if self._model:
                self._model.afterSetBalance()
            self._coin.updateBalance()

    @serializable
    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        if self._label != value:
            self._label = value
            if self._model:
                self._model.afterSetLabel()

    @serializable
    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        if self._comment != value:
            self._comment = value
            if self._model:
                self._model.afterSetComment()

    @serializable
    @property
    def isTxInput(self) -> bool:
        return self._is_tx_input

    @isTxInput.setter
    def isTxInput(self, value: bool) -> None:
        if self._is_tx_input != value:
            self._is_tx_input = value
            if self._model:
                self._model.afterSetIsTxInput()

    @property
    def isReadOnly(self) -> bool:
        return self.privateKey is None

    @serializable
    @property
    def txCount(self) -> int:
        return self._tx_count

    @txCount.setter
    def txCount(self, value: int) -> None:
        if self._tx_count != value:
            self._tx_count = value
            if self._model:
                self._model.afterSetTxCount()

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

        if self._model:
            self._model.beforeAppendTx(tx)
        self._tx_list.append(tx)
        if self._model:
            self._model.afterAppendTx(tx)
        return True

    @serializable
    @property
    def utxoList(self) -> List[Coin.Tx.Utxo]:
        return self._utxo_list

    @utxoList.setter
    def utxoList(self, utxo_list: List[Coin.Tx.Utxo]) -> None:
        if self._utxo_list == utxo_list:
            return

        for utxo in utxo_list:
            utxo.address = self
        self._utxo_list = utxo_list

        if self._model:
            self._model.afterSetUtxoList()
        self._coin.updateUtxoList()

        self.balance = sum(u.amount for u in self._utxo_list)

    @serializable
    @property
    def historyFirstOffset(self) -> str:
        return self._history_first_offset

    @historyFirstOffset.setter
    def historyFirstOffset(self, value: str):
        if self._history_first_offset != value:
            if not value:
                self._clearHistoryOffsets()
            else:
                self._history_first_offset = value
                if self._model:
                    self._model.afterSetHistoryFirstOffset()

    @serializable
    @property
    def historyLastOffset(self) -> str:
        return self._history_last_offset

    @historyLastOffset.setter
    def historyLastOffset(self, value: str):
        if self._history_last_offset != value:
            if not value:
                self._clearHistoryOffsets()
            else:
                self._history_last_offset = value
                if self._model:
                    self._model.afterSetHistoryLastOffset()

    def _clearHistoryOffsets(self) -> None:
        self._history_first_offset = ""
        self._history_last_offset = ""
        if self._model:
            self._model.afterSetHistoryFirstOffset()
            self._model.afterSetHistoryLastOffset()
