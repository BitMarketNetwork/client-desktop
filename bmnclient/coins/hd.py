from __future__ import annotations

from itertools import chain, count
from typing import TYPE_CHECKING

from ..crypto.base58 import Base58
from ..crypto.digest import Hash160Digest, Hmac, Sha512Digest
from ..crypto.secp256k1 import KeyUtils, PrivateKey, PublicKey

if TYPE_CHECKING:
    from typing import Final, Iterator, Optional, Sequence, Tuple, Union
    from .abstract.coin import AbstractCoin


# https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
class HdNode:
    _ROOT_KEY: Final = b"Bitcoin seed"
    _EXTENDED_KEY_SIZE: int = (4 + 1 + 4 + 4 + 32 + 33)
    _HARDENED_MASK = 0x80000000

    def __init__(
            self,
            *,
            key: Union[PrivateKey, PublicKey],
            chain_code: bytes,
            depth: int,
            index: int,
            path: Tuple[int, ...],
            parent_fingerprint: bytes):
        super().__init__()
        self.__key = key
        self.__is_private_key = isinstance(self.__key, PrivateKey)
        self._chain_code = chain_code
        self._depth = depth
        self._index = index
        self._path = path
        self._parent_fingerprint = parent_fingerprint
        self.__identifier: Optional[bytes] = None

        assert len(self._chain_code) == 32
        assert 0x00 <= self._depth <= 0xff
        assert len(self._parent_fingerprint) == 4

    def __eq__(self, other: HdNode) -> bool:
        return (
                isinstance(other, self.__class__)
                and self._chain_code == other._chain_code
                and self._depth == other._depth
                and self._index == other._index
                and self._parent_fingerprint == other._parent_fingerprint
                and self.publicKey == other.publicKey
        )

    def __hash__(self) -> int:
        return hash((
            self._chain_code,
            self._depth,
            self._index,
            self._parent_fingerprint,
            self.publicKey
        ))

    @property
    def publicKey(self) -> PublicKey:
        return self.__key.publicKey if self.__is_private_key else self.__key

    @property
    def privateKey(self) -> Optional[PrivateKey]:
        return self.__key if self.__is_private_key else None

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def index(self) -> int:
        return self._index

    @property
    def identifier(self) -> bytes:
        if self.__identifier is None:
            self.__identifier = Hash160Digest(self.publicKey.data).finalize()
        return self.__identifier

    @property
    def fingerprint(self) -> bytes:
        return self.identifier[:4]

    @classmethod
    def deriveRootNode(cls, seed: bytes) -> Optional[HdNode]:
        key_i = Hmac(cls._ROOT_KEY, Sha512Digest).update(seed).finalize()
        key_i_l = key_i[:32]
        key_i_r = key_i[32:]
        # Protected in secp256k1:
        #   IL is 0 or ≥n
        key = PrivateKey.fromSecretData(key_i_l, is_compressed=True)
        if key is None:
            return None

        return cls(
            key=key,
            chain_code=key_i_r,
            depth=0,
            index=0,
            path=tuple(),
            parent_fingerprint=b"\0" * 4)

    def deriveChildNode(
            self,
            index: int,
            *,
            hardened: bool,
            private: bool) -> Optional[HdNode]:
        if self._depth >= 0xff or (private and self.privateKey is None):
            return None

        if hardened:
            if self.privateKey is None:
                return None
            index = self.toHardenedLevel(index)
            data = b"\x00" + self.privateKey.data
        else:
            data = self.publicKey.data

        index_bytes = KeyUtils.integerToBytes(index, 4)
        if index_bytes is None:
            return None
        data += index_bytes

        assert len(data) == 33 + 4

        key_i = Hmac(self._chain_code, Sha512Digest).update(data).finalize()
        key_i_l = key_i[:32]
        key_i_r = key_i[32:]

        key_integer = KeyUtils.integerFromBytes(key_i_l)
        if key_integer >= KeyUtils.n:
            return None

        if private:
            key_integer += KeyUtils.integerFromBytes(self.privateKey.data)
            key_integer %= KeyUtils.n
            # Protected in secp256k1:
            #   parse256(IL) ≥ n or ki = 0
            key = PrivateKey.fromSecretInteger(key_integer, is_compressed=True)
        else:
            # Protected in secp256k1:
            #   parse256(IL) ≥ n or Ki is the point at infinity
            key = PublicKey.fromPublicInteger(
                key_integer,
                self.publicKey.point,
                is_compressed=True)

        if key is None:
            return None

        return self.__class__(
            key=key,
            chain_code=key_i_r,
            depth=self._depth + 1,
            index=index,
            path=self._path + (index, ),
            parent_fingerprint=self.fingerprint)

    @classmethod
    def fromExtendedKey(cls, key_string: str) -> Tuple[int, Optional[HdNode]]:
        ext_key = Base58.decode(key_string)
        if ext_key is None or len(ext_key) != cls._EXTENDED_KEY_SIZE:
            return 0, None

        offset = 0

        version = KeyUtils.integerFromBytes(ext_key[offset:offset + 4])
        offset += 4
        depth = KeyUtils.integerFromBytes(ext_key[offset:offset + 1])
        offset += 1
        parent_fingerprint = ext_key[offset:offset + 4]
        offset += 4
        index = KeyUtils.integerFromBytes(ext_key[offset:offset + 4])
        offset += 4
        chain_code = ext_key[offset:offset + 32]
        offset += 32
        key_data = ext_key[offset:offset + 33]
        offset += 33

        assert offset == cls._EXTENDED_KEY_SIZE

        if key_data[0] == 0x00:
            key = PrivateKey.fromSecretData(key_data[1:], is_compressed=True)
        else:
            key = PublicKey.fromPublicData(key_data)
            assert key.isCompressed

        if not depth:
            if index or parent_fingerprint != b"\x00" * 4:
                return 0, None

        node = cls(
            key=key,
            chain_code=chain_code,
            depth=depth,
            index=index,
            path=(index, ) if depth else tuple(),
            parent_fingerprint=parent_fingerprint)
        return version, node

    def toExtendedKey(self, version: int, *, private: bool) -> Optional[str]:
        if private and self.privateKey is None:
            return None

        version = KeyUtils.integerToBytes(version, 4)
        depth = KeyUtils.integerToBytes(self._depth, 1)
        index = KeyUtils.integerToBytes(self._index, 4)
        if version is None or depth is None or index is None:
            return None

        result = \
            version \
            + depth \
            + self._parent_fingerprint \
            + index \
            + self._chain_code
        if private:
            result += b"\x00" + self.privateKey.data
        else:
            result += self.publicKey.data

        if len(result) != self._EXTENDED_KEY_SIZE:
            return None
        return Base58.encode(result)

    @classmethod
    def toHardenedLevel(cls, value: int) -> int:
        return (value | cls._HARDENED_MASK) & 0xffffffff

    @classmethod
    def fromHardenedLevel(cls, value: int) -> int:
        return (value & ~cls._HARDENED_MASK) & 0xffffffff

    @classmethod
    def isHardenedLevel(cls, value: int) -> bool:
        return (value & cls._HARDENED_MASK) == cls._HARDENED_MASK

    @property
    def path(self) -> Tuple[int, ...]:
        assert isinstance(self._path, tuple)
        return self._path

    @property
    def isFullPath(self) -> bool:
        return len(self._path) == self._depth

    @classmethod
    def pathFromString(
            cls,
            path: str) -> Tuple[Optional[Tuple[int, ...]], bool]:
        path = path.split("/")
        if not path:
            return tuple(), False

        try:
            result = []
            if path[0] == "m":
                path = path[1:]
                is_full_path = True
            else:
                is_full_path = False

            for level in path:
                if not level:
                    continue

                hardened = False
                if level[-1] in ("'", "h", "H"):
                    level = level[:-1]
                    hardened = True

                if level.startswith("-"):
                    if hardened:
                        return None, False
                    hardened = True

                level = abs(int(level))
                if level > 0xffffffff:
                    return None, False
                if hardened:
                    level = cls.toHardenedLevel(level)

                result.append(level)
            return tuple(result), is_full_path
        except (ValueError, IndexError):
            return None, False

    def pathToString(self, *, hardened_char: str = "H") -> Optional[str]:
        result = []
        if len(self._path) == self._depth:
            result.append("m")
        for level in self._path:
            if level > 0xffffffff:
                return None
            if self.isHardenedLevel(level):
                level = self.fromHardenedLevel(level)
                result.append(str(level) + hardened_char[0])
            else:
                result.append(str(level))
        return "/".join(result)

    def fromPath(
            self,
            path: Union[str, Sequence[int]],
            *,
            private: bool) -> Optional[HdNode]:
        if isinstance(path, str):
            path, is_full_path = self.pathFromString(path)
            if path is None:
                return None
            if is_full_path and self._depth != 0:
                return None

        node = self
        for index in path:
            node = node.deriveChildNode(
                self.fromHardenedLevel(index),
                hardened=self.isHardenedLevel(index),
                private=private)
            if node is None:
                return None
        return node


class HdAddressIterator:
    _EMPTY_ACCOUNT_LIMIT = 2
    _EMPTY_ADDRESS_LIMIT = 6

    def __init__(
            self,
            coin: AbstractCoin,
            *,
            broken_mode: bool = False) -> None:
        self._coin = coin
        self._is_empty_account = True
        self._empty_address_count = 0
        self.broken_mode = broken_mode  # TODO remove in summer 2022
        self._it = self._iterator()

    def __iter__(self) -> Iterator[AbstractCoin.Address]:
        return self._it

    def __next__(self) -> AbstractCoin.Address:
        return next(self._it)

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    def markCurrentAddress(self, is_empty: bool) -> None:
        if is_empty:
            self._empty_address_count += 1
        else:
            self._empty_address_count = 0
            self._is_empty_account = False

    def _iterator(self) -> AbstractCoin.Address:
        if not self._coin.hdNodeList:
            return

        type_list = list(chain(
            filter(
                lambda t:
                    t.value.hdPurpose is not None and t.value.isWitness,
                self._coin.Address.Type),
            filter(
                lambda t:
                    t.value.hdPurpose is not None and not t.value.isWitness,
                self._coin.Address.Type),
        ))

        invalid_address_limit = self._EMPTY_ADDRESS_LIMIT
        empty_address_limit = self._EMPTY_ADDRESS_LIMIT

        if self.broken_mode:
            empty_address_limit *= len(type_list)
            self._empty_address_count = 0
            invalid_address_count = 0
            for address_index in count(0):
                for type_ in type_list:
                    address = self._coin.deriveHdAddress(
                        account=-1,
                        is_change=False,
                        index=address_index,
                        type_=type_)
                    if address is None:
                        invalid_address_count += 1
                        break
                    invalid_address_count = 0
                    yield address
                if invalid_address_count >= invalid_address_limit:
                    break
                if self._empty_address_count >= empty_address_limit:
                    break
            return

        for type_ in type_list:
            empty_account_count = 0
            for account in count(0):
                self._is_empty_account = True

                for change in range(0, 2):
                    self._empty_address_count = 0
                    invalid_address_count = 0
                    for address_index in count(0):
                        address = self._coin.deriveHdAddress(
                            account=account,
                            is_change=change > 0,
                            index=address_index,
                            type_=type_)
                        if address is None:
                            # invalid hd path protection, BIP-0032
                            invalid_address_count += 1
                            if invalid_address_count >= invalid_address_limit:
                                break
                        else:
                            invalid_address_count = 0
                            yield address
                            # controlled by self.markCurrentAddress()
                            if self._empty_address_count >= empty_address_limit:
                                break

                # controlled by self.markCurrentAddress()
                if self._is_empty_account:
                    empty_account_count += 1
                    if empty_account_count >= self._EMPTY_ACCOUNT_LIMIT:
                        break
