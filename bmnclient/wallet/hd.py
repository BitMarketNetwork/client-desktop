from __future__ import annotations

from typing import TYPE_CHECKING

from ..crypto.base58 import Base58
from ..crypto.bech32 import Bech32
from ..crypto.digest import Hash160Digest, Hmac, Sha512Digest
from ..crypto.secp256k1 import KeyUtils, PrivateKey

if TYPE_CHECKING:
    from typing import Final, List, Optional, Sequence, Tuple, Union
    from ..coins.abstract.coin import AbstractCoin


# https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
class HdNode:
    _ROOT_KEY: Final = b"Bitcoin seed"
    _EXTENDED_KEY_SIZE: int = (4 + 1 + 4 + 4 + 32 + 33)
    _HARDENED_MASK = 0x80000000

    def __init__(self, key: key.PrivateKey):
        super().__init__()
        self.key = key
        self.depth = 0
        self.index = 0
        self.chain_code = None
        self.p_fingerprint = b"\x00" * 4

    @classmethod
    def make_hardened_index(cls, index: int):
        assert index is not None
        return index | HARDENED_MASK

    @classmethod
    def make_master(cls, seed: bytes) -> HDNode:
        key_i = Hmac(b"Bitcoin seed", Sha512Digest).update(seed).finalize()
        key_i_l = key_i[:32]
        key_i_r = key_i[32:]

        master = cls(key.PrivateKey.from_secret(key_i_l, None))
        master.chain_code = key_i_r
        return master

    @classmethod
    def from_extended_key(cls, ext_b58: str) -> "HDNode":
        ext_key = util.b58_check_decode(ext_b58)
        if len(ext_key) != 78:
            raise HDError("wrong length of extended key")
        net_pref, ext_key = util.split_bytes(util.get_bytes(ext_key), 4)
        network, prv = coin_network.CoinNetworkBase.from_ex_prefix(
            util.bytes_to_number(net_pref))
        if network is None:
            raise HDError(f"bad network prefix {net_pref} in extended key")
        depth, ext_key = util.split_bytes(ext_key, 1)
        fingerprint, ext_key = util.split_bytes(ext_key, 4)
        index, ext_key = util.split_bytes(ext_key, 4)
        chain_code, ext_key = util.split_bytes(ext_key, 32)
        if prv:
            # extra 0
            key_ = key.PrivateKey(ext_key[1:], network)
        else:
            key_ = key.PublicKey(ext_key, network)
        res = cls(key_)
        res.depth = util.bytes_to_number(depth)
        res.chain_code = chain_code
        res.index = util.bytes_to_number(index)
        res.p_fingerprint = fingerprint
        return res

    @property
    def extended_key(self) -> str:
        res = bytearray()
        res.extend(util.number_to_bytes(
            self.network.EX_PREFIX_PRV if self.is_private else self.network.EX_PREFIX_PUB, 4))
        res.extend(util.number_to_bytes(self.depth, 1))
        res.extend(self.p_fingerprint)
        res.extend(util.number_to_bytes(self.index, 4))
        res.extend(self.chain_code)
        assert 33 == len(self.key.compressed_bytes)
        res.extend(self.key.compressed_bytes)
        return util.b58_check_encode(res)

    @property
    def is_master(self) -> bool:
        return self.depth == 0

    @property
    def is_hardened(self) -> bool:
        return self.index & HARDENED_MASK

    @property
    def chain_id(self) -> str:
        if self.is_master:
            return 'm' if self.is_private else 'M'
        if self.is_hardened:
            return f"{self.index &~ HARDENED_MASK}H"
        return str(self.index)

    @property
    def is_private(self) -> bool:
        return isinstance(self.key, key.PrivateKey)

    def to_address(self, type_: str) -> str:
        return self.key.public_key.to_address(type_)

    @property
    def to_wif(self) -> str:
        return self.key.to_wif

    @property
    def to_hex(self) -> str:
        return self.key.to_hex

    @property
    def fingerprint(self) -> str:
        return self.identifier[:4]

    def make_child_prv(self, index: int, hardened: bool, net: coin_network.CoinNetworkBase = None) -> 'HDNode':
        return self.__derive_private(self.make_hardened_index(index) if hardened else index, net)

    def __derive_private(self, child_index: int, net: coin_network.CoinNetworkBase) -> 'HDNode':
        if not self.is_private:
            raise HDError("private derivation from public key is prohibited")
        is_hardened = child_index & HARDENED_MASK
        child_index_bytes = child_index.to_bytes(length=4, byteorder="big")
        priv = self.key.compressed_bytes
        pub = self.key.public_key.compressed_bytes
        if is_hardened:
            data = priv + child_index_bytes
        else:
            data = pub + child_index_bytes
        I_ = Hmac(self.chain_code, Sha512Digest).update(data).finalize()
        Il, Ir = I_[:32], I_[32:]
        num_Il = util.bytes_to_number(Il)
        p256_Il = (num_Il + util.bytes_to_number(priv)) % SECP256k1_N
        if num_Il >= SECP256k1_N or p256_Il == 0:
            raise HDError()
        child_priv = util.number_to_bytes(p256_Il, 32)
        res = HDNode(key.PrivateKey(child_priv, net or self.network))
        res.chain_code = Ir
        res.depth = self.depth + 1
        res.index = child_index
        res.p_fingerprint = util.hash160(pub)[:4]
        return res

    def __repr__(self):
        return f"depth:{self.depth} index:{self.index}"

    @property
    def network(self):
        return self.key._network

    @property
    def identifier(self):
        return util.hash160(self.key.public_key.compressed_bytes)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return self.depth == other.depth and \
            self.index == other.index and \
            self.chain_code == other.chain_code and \
            self.key == self.key

    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return self.depth != other.depth or \
            self.index != other.index or \
            self.chain_code != other.chain_code or \
            self != other
