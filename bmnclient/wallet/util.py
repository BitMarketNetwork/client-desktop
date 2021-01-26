
import logging
from typing import Union, Tuple, Generator
import enum
import binascii
import sys
import os
import functools
import hashlib
import decimal
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


def ensure_string_or_bytes(data: Union[str, bytes]):
    if not isinstance(data, (str, bytes, bytearray)):
        raise TypeError(f"{type(data)} is not string or bytes")

# https://docs.python.org/3/library/decimal.html#recipes


def moneyfmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = decimal.Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))


def int_to_varint(val: int) -> bytes:
    if val < 253:
        return val.to_bytes(1, 'little')
    elif val <= 65535:
        return b'\xfd'+val.to_bytes(2, 'little')
    elif val <= 4294967295:
        return b'\xfe'+val.to_bytes(4, 'little')
    else:
        return b'\xff'+val.to_bytes(8, 'little')


def random_hex(len: int) -> str:
    # return binascii.b2a_hex(os.urandom(len))
    return os.urandom(len).hex()


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
                'Character %r is not a valid base58 character' % c)
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


def b58_check_encode(data: str) -> bytes:
    signed = get_bytes(data) + sha256d(data)[:4]
    return b58_encode(signed)
    # return (CKey_58.re_encode(CKey_256, signed))


def b58_check_validate(data: str) -> bool:
    ensure_string_or_bytes(data)
    try:
        b58_check_decode(data)
        return True
    except ConvertionError:
        return False


def b58_check_decode(data: bytes) -> bytes:
    bytes_ = b58_decode(data)
    shortened = bytes_[:-4]
    if sha256d(shortened)[:4] == bytes_[-4:]:
        return shortened
    else:
        raise ConvertionError("Hash mismatch")


def number_to_bytes(number: int, length: int) -> bytes:
    return number.to_bytes(length=length, byteorder="big")


def number_to_hex(number: int, length: int) -> str:
    return f"%0{length}x" % number


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
            f'{hrp} does not correspond to a mainnet nor testnet address.')


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


def xor_bytes(data1: bytes, data2: bytes) -> bytes:
    assert len(data1) == len(data2)
    return bytes(a ^ b for (a, b) in zip(data1, data2))


def bytes_to_hex(data: bytes, upper: bool = False) -> str:
    assert sys.version_info >= (3, 5)
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
                raise NotImplementedError("What's padding on 32?")
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
                    raise ConvertionError(f"Bad symbol {d}")
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


class CKey_2(CKey):
    base = KeyBasis.BASE_2
    source = "01"


class CKey_10(CKey):
    base = KeyBasis.BASE_10
    source = "0123456789"


class CKey_16(CKey):
    base = KeyBasis.BASE_16
    source = "0123456789abcdef"


class CKey_32(CKey):
    base = KeyBasis.BASE_32
    source = "abcdefghijklmnopqrstuvwxyz234567"


class CKey_58(CKey):
    """
    dont use it for a while..use b58_encode
    """
    base = KeyBasis.BASE_58
    source = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class CKey_256(CKey):
    base = KeyBasis.BASE_256
    source = ''.join([chr(x) for x in range(256)])

    @classmethod
    def encode(cls, val: int, minlen: int = 0):
        if val < sys.maxsize:
            return val.to_bytes(length=minlen, byteorder="big")
        return super().encode(val, minlen)

    @classmethod
    def decode(cls, string: str):
        return int.from_bytes(string, byteorder="big")
