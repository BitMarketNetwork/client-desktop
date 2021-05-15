import hashlib
import logging
from typing import Any, Optional, Union

from cryptography.exceptions import InvalidSignature
import ecdsa

from . import coin_network, constants, util


log = logging.getLogger(__name__)


class Keybase:
    def __init__(self, data: bytes, network: coin_network.CoinNetworkBase):
        self._data = util.get_bytes(data) if data else None
        self._network = network

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other: Any) -> bool:
        raise NotImplementedError

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def network(self) -> coin_network.CoinNetworkBase:
        return self._network

    @property
    def scriptcode(self) -> str:
        return util.address_to_scriptpubkey(self.to_address("p2pkh"))


class PublicKey(Keybase):
    def __init__(
            self,
            data: Union[bytes, ecdsa.VerifyingKey],
            network: coin_network.CoinNetworkBase,
            compressed: bool = True):
        if not isinstance(data, bytes):
            data = data.to_string(
                "compressed" if compressed else "uncompressed")
        super().__init__(data, network)
        if len(data) not in (33, 65):
            log.critical(f"Bad  input  length:{len(data)} for public key")
            self._data = None

    @property
    def compressed(self) -> bool:
        return 33 == len(self._data)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return self._data == other._data and \
            self._network == other._network

    @property
    def segwit_scriptcode(self) -> str:
        return constants.OP_0 + constants.OP_PUSH_20 + util.hash160(self._data)


class PrivateKey(Keybase):
    def __init__(
            self,
            data: bytes,
            network: coin_network.CoinNetworkBase,
            compressed=True):
        super().__init__(data, network)
        self.eckey: ecdsa.SigningKey = None
        self._compressed = compressed
        if data:
            if len(data) != 32:
                raise KeyError(
                    f"Bad  input  length {len(data)} for private key")
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
    def compressed(self) -> bool:
        return self._compressed

    def sign(self, message, hasher: Optional[callable] = util.sha256):
        message = hasher(message) if hasher else message
        return self.eckey.sign_digest_deterministic(message, sigencode=ecdsa.util.sigencode_der_canonize)

    def verify(self, sig, message, hasher=util.sha256) -> bool:
        message = hasher(message) if hasher else message
        try:
            return self.eckey.verifying_key.verify_digest(sig, message)
        except InvalidSignature:
            return False
        except ecdsa.keys.BadSignatureError:
            return False

    @property
    def key(self):
        return self._data

    @property
    def public_key(self):
        return PublicKey(self.eckey.verifying_key, self._network, self._compressed)

    @property
    def segwit_scriptcode(self) -> str:
        return self.public_key.segwit_scriptcode

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return self._data == other._data and \
            self._network == other._network
