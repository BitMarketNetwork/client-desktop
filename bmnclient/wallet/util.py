import binascii
from typing import Union


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


def bytes_to_hex(data: bytes, upper: bool = False) -> str:
    hexed = binascii.hexlify(data).decode()
    return hexed.upper() if upper else hexed


def hex_to_bytes(hexed: str) -> bytes:
    if len(hexed) & 1:
        hexed = '0' + hexed
    return bytes.fromhex(hexed)
