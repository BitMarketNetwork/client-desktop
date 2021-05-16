# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..crypto.base58 import Base58
from ..crypto.bech32 import Bech32
from ..crypto.digest import Hash160Digest, Hmac, Sha512Digest
from ..crypto.secp256k1 import KeyUtils, PrivateKey, PublicKey

if TYPE_CHECKING:
    from typing import Final, List, Optional, Sequence, Tuple, Union
    from ..coins.abstract.coin import AbstractCoin


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
            parent_fingerprint: bytes):
        super().__init__()
        self.__key = key
        self.__is_private_key = isinstance(self.__key, PrivateKey)
        self._chain_code = chain_code
        self._depth = depth
        self._index = index
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
            index |= self._HARDENED_MASK
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

        node = cls(
            key=key,
            chain_code=chain_code,
            depth=depth,
            index=index,
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
    def levelsPathFromString(cls, path: str) -> Optional[List[int]]:
        path = path.split("/")
        if not path:
            return []

        try:
            if path[0] == "m":
                path = path[1:]

            result = []
            for level in path:
                if not level:
                    continue

                hardened = False
                if level[-1] in ("'", "h", "H"):
                    level = level[:-1]
                    hardened = True

                if level.startswith("-"):
                    if hardened:
                        return None
                    hardened = True

                level = abs(int(level))
                if hardened:
                    level |= cls._HARDENED_MASK

                if level > 0xffffffff:
                    return None
                result.append(level)
            return result
        except (ValueError, IndexError):
            return None

    def fromLevelsPath(
            self,
            path: Union[str, Sequence],
            *,
            private: bool) -> Optional[HdNode]:
        if isinstance(path, str):
            path = self.levelsPathFromString(path)
            if path is None:
                return None

        node = self
        for index in path:
            node = node.deriveChildNode(
                index & ~self._HARDENED_MASK,
                hardened=(index & self._HARDENED_MASK) == self._HARDENED_MASK,
                private=private)
            if node is None:
                return None
        return node

    def createAddress(
            self,
            coin: AbstractCoin,
            type_: AbstractCoin.Address.Type,
            **kwargs) -> Optional[AbstractCoin.Address]:
        if type_.value.encoding == coin.Address.Encoding.BASE58:
            version = KeyUtils.integerToBytes(type_.value.version, 1)
            if version is None:
                return None
            name = Hash160Digest(self.publicKey.data).finalize()
            name = Base58.encode(version + name)
        elif type_.value.encoding == coin.Address.Encoding.BECH32:
            if not self.publicKey.isCompressed:
                return None
            name = Hash160Digest(self.publicKey.data).finalize()
            name = Bech32.encode(coin.Address.hrp, type_.value.version, name)
        else:
            return None

        return coin.Address(
            coin,
            name=name,
            type_=type_,
            key=self,
            **kwargs)
