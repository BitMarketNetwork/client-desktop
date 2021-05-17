import binascii
import hashlib
from typing import Union

from . import coin_network, constants
from ..crypto.base58 import Base58
from ..crypto.bech32 import Bech32


def get_bytes(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        return data.encode('utf-8')
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"{type(data)} are not bytes")
    return data


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
                address_data[1:] +
                constants.OP_EQUALVERIFY + constants.OP_CHECKSIG)
    elif version in coin_network.SCRIPT_HASH_LIST:
        return (constants.OP_HASH160 + constants.OP_PUSH_20 +
                address_data[1:] +
                constants.OP_EQUAL)


def bytes_to_hex(data: bytes, upper: bool = False) -> str:
    hexed = binascii.hexlify(data).decode()
    return hexed.upper() if upper else hexed


def hex_to_bytes(hexed: str) -> bytes:
    if len(hexed) & 1:
        hexed = '0' + hexed
    return bytes.fromhex(hexed)
