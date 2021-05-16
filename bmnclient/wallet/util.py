
import logging
from typing import Union, Tuple, Generator
import enum
import binascii
import functools
import hashlib
from . import coin_network
from . import constants
from ..crypto.bech32 import Bech32

log = logging.getLogger(__name__)


class ConvertionError(Exception):
    pass


def get_bytes(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        return data.encode('utf-8')
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"{type(data)} are not bytes")
    return data


def int_to_varint(val: int) -> bytes:
    if val < 253:
        return val.to_bytes(1, 'little')
    elif val <= 65535:
        return b'\xfd'+val.to_bytes(2, 'little')
    elif val <= 4294967295:
        return b'\xfe'+val.to_bytes(4, 'little')
    else:
        return b'\xff'+val.to_bytes(8, 'little')


def read_var_int(stream: bytes) -> int:
    val = int(bytes_to_hex(stream[0:1]), base=16)
    if val < 253:
        return val, stream[1:]
    return read_as_int(stream[1:], 2**(val-252))


def read_var_string(stream: bytes) -> str:
    size, stream = read_var_int(stream)
    return split_bytes(stream, size)


def read_as_int(stream: bytes, bytes_: int) -> int:
    return int(bytes_to_hex(stream[0:bytes_][::-1]), base=16), stream[bytes_:]


def read_segwit_string(stream: str) -> Tuple[bytes, bytes]:
    bytes_, stream = read_var_int(stream)
    witness, stream = split_bytes(stream, bytes_)
    return int_to_varint(bytes_) + witness, stream


def hash160(data: Union[str, bytes]) -> bytes:
    rh = hashlib.new('ripemd160', hashlib.sha256(get_bytes(data)).digest())
    return rh.digest()


def sha256(data: Union[str, bytes]) -> bytes:
    return bytes(hashlib.sha256(get_bytes(data)).digest())


def sha256d(data: Union[str, bytes]) -> bytes:
    return bytes(sha256(sha256(get_bytes(data))))


def b58_encode(data: bytes) -> str:
    n = int('0x0' + binascii.hexlify(data).decode('utf8'), 16)
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(CKey_58.source[r])
    res = ''.join(res[::-1])
    pad = 0
    for c in data:
        if c == 0:
            pad += 1
        else:
            break
    return CKey_58.source[0] * pad + res


def b58_decode(data: str) -> bytes:
    if not data:
        return b''
    n = 0
    for c in data:
        n *= 58
        if c not in CKey_58.source:
            raise ConvertionError(
                'character %r is not a valid base58 character' % c)
        digit = CKey_58.source.index(c)
        n += digit
    h = '%x' % n
    if len(h) % 2:
        h = '0' + h
    res = binascii.unhexlify(h.encode('utf8'))
    pad = 0
    for c in data[:-1]:
        if c == CKey_58.source[0]:
            pad += 1
        else:
            break
    return b'\x00' * pad + res


def b58_check_encode(data: str) -> str:
    signed = get_bytes(data) + sha256d(data)[:4]
    return b58_encode(signed)


def b58_check_decode(data: bytes) -> bytes:
    bytes_ = b58_decode(data)
    shortened = bytes_[:-4]
    if sha256d(shortened)[:4] == bytes_[-4:]:
        return shortened
    else:
        raise ConvertionError("hash mismatch")


def number_to_bytes(number: int, length: int) -> bytes:
    return number.to_bytes(length=length, byteorder="big")


def bytes_to_number(bytes_: bytes) -> int:
    # assert isinstance(bytes_,bytes)
    return int.from_bytes(bytes_, byteorder="big")


def number_to_unknown_bytes(num: int, byteorder: str = 'big') -> bytes:
    """Converts an int to the least number of bytes as possible."""
    return num.to_bytes((num.bit_length() + 7) // 8 or 1, byteorder)


def script_push(val: int) -> bytes:
    if val <= 75:
        return number_to_unknown_bytes(val)
    elif val < 256:
        return b'\x4c'+number_to_unknown_bytes(val)
    elif val < 65536:
        return b'\x4d'+val.to_bytes(2, 'little')
    else:
        return b'\x4e'+val.to_bytes(4, 'little')


def get_version(address: str) -> str:
    hrp, _, _ = Bech32.decode(address)
    if hrp is None:
        hrp = b58_check_decode(address)[:1]
    if (hrp in coin_network.MAIN_NET_PREFIX_SET or
            hrp in coin_network.MAIN_BECH_HRP_SET):
        return 'main'
    elif (hrp in coin_network.TEST_NET_PREFIX_SET or
          hrp in coin_network.TEST_BECH_HRP_SET):
        return 'test'
    else:
        raise ConvertionError(
            f'{hrp} does not correspond to a mainnet nor testnet address')


def address_to_scriptpubkey(address: str) -> str:
    # Raise ConvertionError if we cannot identify the address.
    get_version(address)
    try:
        version = b58_check_decode(address)[:1]
    except ConvertionError:
        hrp, witver, data = Bech32.decode(address)
        return bytes([witver + 0x50 if witver else 0, len(data)]) + data

    if version in coin_network.PUBLIC_HASH_LIST:
        return (constants.OP_DUP + constants.OP_HASH160 + constants.OP_PUSH_20 +
                address_to_public_key_hash(address) +
                constants.OP_EQUALVERIFY + constants.OP_CHECKSIG)
    elif version in coin_network.SCRIPT_HASH_LIST:
        return (constants.OP_HASH160 + constants.OP_PUSH_20 +
                address_to_public_key_hash(address) +
                constants.OP_EQUAL)


def address_to_public_key_hash(address) -> str:
    # Raise ConvertionError if we cannot identify the address.
    get_version(address)
    return b58_check_decode(address)[1:]


def bytes_to_hex(data: bytes, upper: bool = False) -> str:
    hexed = binascii.hexlify(data).decode()
    return hexed.upper() if upper else hexed


def hex_to_bytes(hexed: str) -> bytes:
    if len(hexed) & 1:
        hexed = '0' + hexed
    return bytes.fromhex(hexed)

# Slicing


def split_bytes(stream: bytes, index: int) -> Tuple[bytes, bytes]:
    return stream[:index], stream[index:]


def chunk_data(data: Union[bytes, str], size: int) -> Generator:
    return (data[i:i + size] for i in range(0, len(data), size))


class KeyBasis(enum.IntEnum):
    BASE_2 = 2
    BASE_10 = 10
    BASE_16 = 16
    BASE_32 = 32
    BASE_58 = 58
    BASE_256 = 256


class CKey:
    base = None
    source = None

    @classmethod
    def make(cls, base: KeyBasis):
        return next(val for _, val in globals().items() if isinstance(val, type) and issubclass(val, cls) and base == val.base)

    @classmethod
    def encode(cls, val: int, minlen: int = 0) -> Union[bytes, str]:
        minlen = int(minlen)
        indexes = []
        while val > 0:
            val, mod = divmod(val, cls.base)
            indexes.append(ord(cls.source[mod]))
        if len(indexes) < minlen:
            if cls.base == KeyBasis.BASE_32:
                raise NotImplementedError("what's padding on 32?")
            indexes += [0] * (minlen - len(indexes))
        result_bytes = bytes(indexes[::-1])
        if cls.base == KeyBasis.BASE_256:
            return result_bytes
        return ''.join([chr(y) for y in result_bytes])

    @classmethod
    def decode(cls, txt: str):
        if cls.base == KeyBasis.BASE_256:
            if isinstance(txt, str):
                txt = bytes(bytearray.fromhex(txt))

            def ex(s, d):
                return s*cls.base+d
        else:
            def ex(s, d):
                idx = cls.source.find(d if isinstance(d, str) else chr(d))
                if idx < 0:
                    raise ConvertionError(f"bad symbol {d}")
                return s * cls.base + idx
            # ex = lambda d: cls.source.find(d)
        if cls.base == KeyBasis.BASE_16:
            txt = txt.lower()
        return functools.reduce(ex, txt, 0)

    @classmethod
    def re_encode(cls, from_: type, string: str, minlen: int = 0):
        """
        encode one base to another
        """
        return cls.encode(from_.decode(string), minlen=minlen)


class CKey_58(CKey):
    """
    dont use it for a while..use b58_encode
    """
    base = KeyBasis.BASE_58
    source = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
