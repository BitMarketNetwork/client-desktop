# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from .digest import Sha256DoubleDigest

if TYPE_CHECKING:
    from typing import Final, Optional


class Base58:
    _CHAR_LIST: Final = \
        "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"  # noqa
    _CHAR_LIST_MAP: Final = {c: i for i, c in enumerate(_CHAR_LIST)}
    _BASE: Final = len(_CHAR_LIST)
    _CHECKSUM_SIZE: Final = 4

    @classmethod
    def encode(cls, source: bytes, check: bool = True) -> str:
        offset = 0
        while offset < len(source):
            if not source[offset] == 0x00:
                break
            offset += 1

        if check:
            source += cls._digest(source)

        value = int.from_bytes(source[offset:], "big")
        result = []
        while value:
            value, mod = divmod(value, cls._BASE)
            result.append(cls._CHAR_LIST[mod:mod + 1])

        return cls._CHAR_LIST[0:1] * offset + "".join(reversed(result))

    @classmethod
    def decode(cls, source: str, check: bool = True) -> Optional[bytes]:
        offset = 0
        while offset < len(source):
            if not source[offset] == cls._CHAR_LIST[0]:
                break
            offset += 1

        value = 0
        try:
            for c in source[offset:]:
                value = value * cls._BASE + cls._CHAR_LIST_MAP[c]
        except KeyError:
            return None

        result = []
        while value:
            value, mod = divmod(value, 256)
            result.append(mod)

        result = b"\0" * offset + bytes(reversed(result))

        if check:
            digest = result[-cls._CHECKSUM_SIZE:]
            result = result[:-cls._CHECKSUM_SIZE]
            if not result or cls._digest(result) != digest:
                return None
        return result

    @classmethod
    def _digest(cls, source: bytes) -> bytes:
        return Sha256DoubleDigest(source).finalize()[:cls._CHECKSUM_SIZE]
