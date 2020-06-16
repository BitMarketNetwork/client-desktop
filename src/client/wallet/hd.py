
import logging

from typing import Optional
from . import db_entry
from . import key_format
from . import util
from . import coin_network
from . import key
log = logging.getLogger(__name__)

SECP256k1_N = 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFE_BAAEDCE6_AF48A03B_BFD25E8C_D0364141
UINT_MAX = (1 << 32) - 1
HARDENED_MASK = 0x80000000

key_count = 0

class HDError(Exception):
    pass

class HDNode(key.AddressBase):

    def __init__(self, key : key.PrivateKey, parent = None):
        """
        TODO:
        There is an issue with parent.
        Be careful!
        When address hd made from coin hd - then parent is coin hd
        But when addres hd made from extended key(import for example), then parent is address instance
        """
        super().__init__()
        self._parent = parent
        self.key = key
        self.depth = 0
        self.index = 0
        self.chain_code = None
        self.p_fingerprint = b"\x00" * 4
        self._children_count = 0

    @classmethod
    def make_hardened_index(cls, index: int):
        return index | HARDENED_MASK

    @classmethod
    def make_master(cls, seed: int, network: coin_network.CoinNetworkBase) -> "HDNode":
        I = util.hmac_hash(b"Bitcoin seed", seed)
        Il, Ir = I[:32], I[32:]
        master = cls(key.PrivateKey.from_secret(Il, network))
        master.chain_code = Ir
        return master

    @classmethod
    def from_extended_key(cls, ext_b58: str, parent) -> "HDNode":
        ext_key = util.b58_check_decode(ext_b58)
        if len(ext_key) != 78:
            raise HDError("Wrong length of extended key")
        net_pref, ext_key = util.split_bytes(util.get_bytes(ext_key), 4)
        network, prv = coin_network.CoinNetworkBase.from_ex_prefix(
            util.bytes_to_number(net_pref))
        if network is None:
            raise HDError(f"Bad network prefix {net_pref} in extended key")
        depth, ext_key = util.split_bytes(ext_key, 1)
        fingerprint, ext_key = util.split_bytes(ext_key, 4)
        index, ext_key = util.split_bytes(ext_key, 4)
        chain_code, ext_key = util.split_bytes(ext_key, 32)
        if prv:
            # extra 0
            key_ = key.PrivateKey(ext_key[1:], network)
        else:
            key_ = key.PublicKey(ext_key, network)
        res = cls(key_, parent)
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
    def chain_path(self) -> str:
        if self.is_master:
            return f"{self.chain_id}"
        if self._parent is None:
            return ""
        return f"{self._parent.chain_path}/{self.chain_id}"

    @property
    def is_private(self) -> bool:
        return isinstance(self.key, key.PrivateKey)

    def to_address(self, type_, witver=0) -> str:
        return self.key.public_key.to_address(type_, witver)

    @property
    def to_wif(self) -> str:
        return self.key.to_wif

    @property
    def public_hd_key(self) -> "HDNode":
        """
        avoid calling it if you need jsut public key
        call instead self.key.public_key
        """
        if self.is_private:
            copy = HDNode(
                key=self.key.public_key,
                parent=self,
            )
            copy.chain_code = self.chain_code
            copy.depth = self.depth
            copy.index = self.index
            copy.p_fingerprint = self.p_fingerprint
            return copy
        return self

    @property
    def fingerprint(self) -> str:
        return self.identifier[:4]

    @property
    def children_count(self) -> int:
        return self._children_count

    def make_child_prv(self, index: int, hardened: bool, net: coin_network.CoinNetworkBase = None) -> 'HDNode':
        return self._derive_private(self.make_hardened_index(index) if hardened else index, net)

    def _derive_private(self, child_index: int, net) -> 'HDNode':
        """
        """
        if not self.is_private:
            raise HDError("Private derivation from public key is prohibited")
        is_hardened = child_index & HARDENED_MASK
        child_index_bytes = child_index.to_bytes(length=4, byteorder="big")
        priv = self.key.compressed_bytes
        pub = self.key.public_key.compressed_bytes
        if is_hardened:
            data = priv + child_index_bytes
        else:
            data = pub + child_index_bytes
        I_ = util.hmac_hash(self.chain_code, data)
        Il, Ir = I_[:32], I_[32:]
        num_Il = util.bytes_to_number(Il)
        p256_Il = (num_Il + util.bytes_to_number(priv)) % SECP256k1_N
        if num_Il >= SECP256k1_N or p256_Il == 0:
            raise HDError()
        child_priv = util.number_to_bytes(p256_Il,32)
        res = HDNode(key.PrivateKey(child_priv, net or self.network), self)
        # ep = pybmn.ECPoint(pub)
        # ep.g_mul(Il)
        # assert ep.content == res.key.public_key.compressed_bytes
        res.chain_code = Ir
        res.depth = self.depth + 1
        res.index = child_index
        res.p_fingerprint = util.hash160(pub)[:4]
        self._children_count += 1
        return res

    def _derive_public(self, child_index: int):
        """
        TODO:
        There's a hole here -> no boundary checks!
        Not tested !
        """
        if not self.is_private:
            raise HDError("Private derivation from public key is prohibited")
        is_hardened = child_index & HARDENED_MASK
        child_index = child_index.to_bytes(length=4, byteorder="big")
        priv = self.key.compressed_bytes
        pub = self.key.public_key.compressed_bytes
        if is_hardened:
            data = priv + child_index
        else:
            data = pub + child_index
        I = util.hmac_hash(self.chain_code, data)
        Il, Ir = I[:32], I[32:]
        num_Il = util.bytes_to_number(Il)
        p256_Il = (num_Il + util.bytes_to_number(priv)) % SECP256k1_N
        if num_Il >= SECP256k1_N or p256_Il == 0:
            raise HDError()
        ep = pybmn.ECPoint(pub)
        ep.g_mul(Il)
        child_pub = ep.content
        res = HDNode(key.PublicKey(child_pub, self._network),
                     self._network, self)
        res.chain_code = Ir
        res.depth += 1
        res.child_index = child_index
        res.p_fingerprint = self.fingerprint
        self._children_count += 1
        return res

    def from_chain_path(self, path):
        """
        path is string path or list<int>
        """
        if isinstance(path, str):
            path = self.convert_chain_path(path)
        if not self.is_master:
            # if we're not master - then cut head of path
            parent = self
            sub_path = []
            while not parent.is_master:
                sub_path.append(parent.index)
                parent = parent.parent
            for i in reversed(sub_path):
                if i == path[0]:
                    path = path[1:]
                else:
                    raise HDError(f"Wrong parent {1}")
        #
        log.debug("bip32 path %s net:%s", path, self.network)
        key = self
        for child_index in path:
            key = key._derive_private(child_index, self.network)
        return key

    @staticmethod
    def convert_chain_path(path: str):
        """
        Convert bip32 path to list  integers with  flags
        m/0/-1/1' -> [0, 0x80000001, 0x80000001]
        based on code in trezorlib
        """
        if not path:
            return []
        if path.endswith("/"):
            path = path[:-1]
        path = path.split('/')
        if path[0] == "m":
            path = path[1:]
        result = []
        for x in path:
            if x == '':
                continue
            prime = 0
            if x.endswith("'") or x.endswith("h") or x.endswith("H"):
                x = x[:-1]
                prime = HARDENED_MASK
            if x.startswith('-'):
                if prime:
                    raise HDError(
                        f"bip32 path child index is signalling hardened level in multiple ways")
                prime = HARDENED_MASK
            child_index = abs(int(x)) | prime
            if child_index > UINT_MAX:
                raise HDError(
                    f"bip32 path child index too large: {child_index} > {UINT_MAX}")
            result.append(child_index)
        return result

    def __repr__(self):
        return f"depth:{self.depth} index:{self.index}"

    def from_args(self, arg_iter: iter):
        raise NotImplementedError()

    @property
    def parent(self):
        return self._parent

    @property
    def network(self):
        return self.key._network

    @property
    def identifier(self):
        return util.hash160(self.key.public_key.compressed_bytes)

    @property
    def fingerprint(self):
        return self.identifier[:4]

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
