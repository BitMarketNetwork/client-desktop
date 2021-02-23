import abc
import enum
import hashlib
import logging
from typing import Any, Optional, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
import ecdsa
from ..crypto.bech32 import Bech32

from . import coin_network, constants, util


log = logging.getLogger(__name__)


class KeyError(Exception):
    pass


class AddressType(enum.IntEnum):
    """
    p2pkh, p2sh, p2wpkh, p2wsh, witness_unknown, unknown.
    """
    P2PKH = enum.auto()
    P2SH = enum.auto()
    P2WPKH = enum.auto()
    P2WSH = enum.auto()
    WITNESS_UNKNOWN = enum.auto()
    UNKNOWN = enum.auto()

    @classmethod
    def make(cls, string: str) -> 'AddressType':
        return cls[string.upper()]

    @property
    def lower(self) -> str:
        return str(self.name).lower()


class AddressMalformedError(Exception):
    pass


class AddressString:
    @classmethod
    def is_segwit(cls, address: str) -> bool:
        hrp, _, _ = Bech32.decode(address)
        return hrp is not None


class AbstractAddress(abc.ABC):

    @abc.abstractproperty
    def to_address(self, type_):
        pass

    @property
    def P2PKH(self) -> str:
        if not hasattr(self, "_p2pkh"):
            self._p2pkh = self.to_address(
                AddressType.P2PKH)
        return self._p2pkh

    @property
    def P2WPKH(self) -> str:
        if not hasattr(self, "_p2wpkh"):
            self._p2wpkh = self.to_address(
                AddressType.P2WPKH)
        return self._p2wpkh

    @property
    def scriptcode(self) -> str:
        return util.address_to_scriptpubkey(self.P2PKH)


class Keybase(abc.ABC):

    def __init__(self, data: bytes, network: coin_network.CoinNetworkBase):
        self._data = util.get_bytes(data) if data else None
        self._network = network

    def __str__(self) -> str:
        return self.to_hex

    def __len__(self) -> int:
        return len(self._data)

    @abc.abstractproperty
    def is_valid(self):
        pass

    @abc.abstractproperty
    def compressed_bytes(self):
        pass

    @abc.abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @property
    def is_multi_sig(self) -> bool:
        """
        for future
        """
        return False

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def to_hex(self) -> str:
        return util.bytes_to_hex(self._data, False)

    @property
    def network(self) -> coin_network.CoinNetworkBase:
        return self._network


class PublicKey(Keybase, AbstractAddress):

    # def __init__(self, data: Union[bytes, ec.EllipticCurvePublicKey], network: coin_network.CoinNetworkBase, compressed: bool = True):
    def __init__(self, data: Union[bytes, ecdsa.VerifyingKey], network: coin_network.CoinNetworkBase, compressed: bool = True):
        if not isinstance(data, bytes):
            # data = data.public_bytes( encoding=serialization.Encoding.X962, format=serialization.PublicFormat.CompressedPoint if compressed else serialization.PublicFormat.UncompressedPoint,)
            data = data.to_string(
                "compressed" if compressed else "uncompressed")
        super().__init__(data, network)
        if len(data) not in (33, 65):
            # raise KeyError(f"Bad  input  length:{len(data)} for public key")
            log.critical(f"Bad  input  length:{len(data)} for public key")
            self._data = None

    @property
    def is_valid(self) -> bool:
        return not not self._data

    @property
    def compressed_bytes(self) -> bytes:
        """ 33 bytes """
        return self._data

    @property
    def compressed(self) -> bool:
        return self.is_valid and 33 == len(self._data)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return self._data == other._data and \
            self._network == other._network

    def to_address(self, type_: AddressType, witver: int = 0) -> str:
        if self._data:
            if type_ == AddressType.P2PKH:
                return util.b58_check_encode(self._network.ADDRESS_BYTE_PREFIX + util.hash160(self._data))
            if type_ == AddressType.P2WPKH:
                if self.compressed:
                    if len(self._data) != 33:
                        raise KeyError("SEGWIT only for compressed keys")
                    return Bech32.encode(self._network.BECH32_HRP, witver, util.hash160(self._data))
                    # return util.b58_check_encode(self._network.SCRIPT_BYTE_PREFIX + util.hash160(b'\x00\x14' + util.hash160(self._data)))
            else:
                raise KeyError(f"Unsupported address type {type_}")

    @property
    def segwit_scriptcode(self) -> str:
        return constants.OP_0 + constants.OP_PUSH_20 + util.hash160(self._data)


class PrivateKey(Keybase, AbstractAddress):
    EC_CURVE = ec.SECP256K1()

    def __init__(self, data: bytes, network: coin_network.CoinNetworkBase, compressed=True):
        super().__init__(data, network)
        # self.eckey: ec.EllipticCurvePrivateKey = None
        self.eckey: ecdsa.SigningKey = None
        self._compressed = compressed
        if data:
            if len(data) != 32:
                raise KeyError(
                    f"Bad  input  length {len(data)} for private key")
            # self.eckey = ec.derive_private_key( util.bytes_to_number(data), self.EC_CURVE, default_backend(),)
            self.eckey = ecdsa.SigningKey.from_string(
                data,
                curve=ecdsa.SECP256k1,
                hashfunc=hashlib.sha256,
            )

    @classmethod
    def from_secret(cls, secret: bytes, network: coin_network.CoinNetworkBase) -> "PrivateKey":
        number = util.bytes_to_number(secret)

        try:
            result = cls(None, network=network)
            result.eckey = ecdsa.SigningKey.from_secret_exponent(
                number,
                curve=ecdsa.SECP256k1,
                hashfunc=hashlib.sha256,
            )
            result._data = result.eckey.to_string()
            return result
        except ecdsa.MalformedPointError as err:
            log.error(f"Can't make prv key from secret: {err}")
            return None

    @classmethod
    def from_wif(cls, wif: str, net: coin_network.CoinNetworkBase = None) -> "PrivateKey":
        try:
            prv = util.b58_check_decode(wif)
        except util.ConvertionError as ce:
            raise KeyError from ce
        if net is None:
            net = coin_network.CoinNetworkBase.from_prv_version(prv[:1])
        if net is None:
            raise KeyError(f"Unknown WIF version {prv[:1]}")
        if len(wif) == 52 and prv[-1] == 1:
            prv, compressed = prv[1:-1], True
        else:
            prv, compressed = prv[1:], False
        return cls(prv, net, compressed)

    @property
    def to_wif(self) -> str:
        if self._network is None:
            raise KeyError("Empty network")
        if self.compressed:
            suffix = constants.PRIVATE_KEY_COMPRESSED_PUBKEY
        else:
            suffix = b''
        private_key = self._network.PRIVATE_KEY + self._data + suffix
        return util.b58_check_encode(private_key)

    def can_sign_unspent(self, utxo: "Unspent") -> bool:
        """
        Server doesn't give us scripts
        """
        return True
        # if utxo.script is None:
        #     # log.debug("Skip key sign check for utxo")
        #     return True
        # script = util.bytes_to_hex(util.address_to_scriptpubkey(self.P2PKH))
        # if utxo.script == script:
        #     return True
        # if self.P2WPKH is not None:
        #     segwit_script = util.bytes_to_hex(
        #         util.address_to_scriptpubkey(self.P2WPKH))
        #     if utxo.script == segwit_script:
        #         return True
        #     else:
        #         log.warning(f"@@@@ {utxo.script} != {segwit_script} @@@@@")
        # return False

    @property
    def compressed(self) -> bool:
        return self._compressed

    def sign(self, message, hasher: Optional[callable] = util.sha256):
        message = hasher(message) if hasher else message
        # return self.eckey.sign(message.encode(), ec.ECDSA(hashes.SHA256()))
        # return self.eckey.sign_digest(message , hashfunc = hashlib.sha256)
        return self.eckey.sign_digest_deterministic(message, sigencode=ecdsa.util.sigencode_der_canonize)

    def verify(self, sig, message, hasher=util.sha256) -> bool:
        message = hasher(message) if hasher else message
        try:
            # sig_meth = ec.ECDSA(hashes.SHA256())
            # self.eckey.public_key().verify(sig, message, sig_meth)
            return self.eckey.verifying_key.verify_digest(sig, message)
        except InvalidSignature:
            return False
        except ecdsa.keys.BadSignatureError:
            return False

    @property
    def is_valid(self) -> bool:
        return True

    @property
    def key(self):
        return self._data

    @property
    def public_key(self):
        # return PublicKey(self.eckey.public_key(), self._network, self._compressed)
        return PublicKey(self.eckey.verifying_key, self._network, self._compressed)

    def to_address(self, type_: AddressType, witver: int = 0) -> str:
        return self.public_key.to_address(type_, witver)

    @property
    def segwit_scriptcode(self) -> str:
        return self.public_key.segwit_scriptcode

    @property
    def compressed_bytes(self) -> bytes:
        """ 33 bytes """
        return b'\00' + self.key

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return self._data == other._data and \
            self._network == other._network
