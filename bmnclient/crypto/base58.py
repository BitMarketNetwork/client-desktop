# JOK++
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .digest import Sha256Digest

if TYPE_CHECKING:
    from typing import Final


class Base58:
    CHAR_LIST: Final = \
        "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"  # noqa
    CHAR_LIST_MAP: Final = {c: i for i, c in enumerate(CHAR_LIST)}
    BASE: Final = len(CHAR_LIST)
    CHECKSUM_SIZE: Final = 4

    @classmethod
    def encode(cls, source: bytes, check=True) -> str:
        offset = 0
        while offset < len(source):
            if not source[offset] == 0x00:
                break
            offset += 1

        if check:
            source += cls._digest(source)

        value = int.from_bytes(source[offset:], byteorder='big')
        result = []
        while value:
            value, mod = divmod(value, cls.BASE)
            result.append(cls.CHAR_LIST[mod:mod + 1])

        return cls.CHAR_LIST[0:1] * offset + "".join(reversed(result))

    @classmethod
    def decode(cls, source: str, check=True) -> Optional[bytes]:
        offset = 0
        while offset < len(source):
            if not source[offset] == cls.CHAR_LIST[0]:
                break
            offset += 1

        value = 0
        try:
            for c in source[offset:]:
                value = value * cls.BASE + cls.CHAR_LIST_MAP[c]
        except KeyError:
            return None

        result = []
        while value:
            value, mod = divmod(value, 256)
            result.append(mod)

        result = b"\0" * offset + bytes(reversed(result))

        if check:
            digest = result[-cls.CHECKSUM_SIZE:]
            result = result[:-cls.CHECKSUM_SIZE]
            if not result or cls._digest(result) != digest:
                return None
        return result

    @classmethod
    def _digest(cls, source: bytes) -> bytes:
        digest0 = Sha256Digest()
        digest1 = Sha256Digest()
        digest0.update(source)
        digest1.update(digest0.finalize())
        return digest1.finalize()[:cls.CHECKSUM_SIZE]
