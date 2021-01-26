# JOK+
from typing import Optional, Tuple, Union


class Bech32:
    CHAR_LIST = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    CHECKSUM_SIZE = 6
    MAX_SIZE = 90

    @classmethod
    def encode(
            cls,
            hrp: str,
            version: int,
            data: bytes,
            *,
            strict=True) -> Optional[str]:
        if not hrp or not cls._verifyVersion(version, data, strict):
            return None

        data = cls._convertBits(data, 8, 5)
        if data is None:
            return None
        result_size = len(hrp) + 1 + 1 + len(data) + cls.CHECKSUM_SIZE
        if result_size > cls.MAX_SIZE:
            return None

        data = bytes([version]) + data
        data += cls._createChecksum(hrp, data)
        data = hrp + "1" + "".join(cls.CHAR_LIST[i] for i in data)
        assert result_size == len(data)
        return data

    @classmethod
    def decode(
            cls,
            source: str,
            *,
            strict=True) \
            -> Union[Tuple[None, None, None], Tuple[str, int, bytes]]:
        result_none = (None, None, None)
        if len(source) > cls.MAX_SIZE:
            return result_none

        source = source.lower()
        separator = source.rfind("1")
        if separator < 1 or separator + 1 + cls.CHECKSUM_SIZE >= len(source):
            return result_none

        data = []
        for c in source[separator + 1:]:
            c = cls.CHAR_LIST.find(c)
            if c < 0:
                return result_none
            data.append(c)

        hrp = source[:separator]
        version = data[0]
        data = bytes(data)

        if not cls._verifyChecksum(hrp, data):
            return result_none

        data = cls._convertBits(data[1:-cls.CHECKSUM_SIZE], 5, 8, False)
        if data is None or not cls._verifyVersion(version, data, strict):
            return result_none

        return hrp, version, data

    @classmethod
    def _verifyVersion(cls, version: int, data: bytes, strict) -> bool:
        if not 0 <= version <= 16:
            return False
        if strict:
            if not 2 <= len(data) <= 40:
                return False
            if version == 0 and len(data) != 20 and len(data) != 32:
                return False
        return True

    @classmethod
    def _hrpExpand(cls, hrp: str) -> bytes:
        high = [ord(c) >> 5 for c in hrp]
        low = [ord(c) & 31 for c in hrp]
        return bytes(high + [0] + low)

    @classmethod
    def _createChecksum(cls, hrp: str, data: bytes) -> bytes:
        checksum = cls._polyMod(cls._hrpExpand(hrp), 1)
        checksum = cls._polyMod(data, checksum)
        checksum = cls._polyMod(b"\0" * cls.CHECKSUM_SIZE, checksum)
        checksum ^= 1
        return bytes(
            (checksum >> 5 * (5 - i)) & 31 for i in range(cls.CHECKSUM_SIZE))

    @classmethod
    def _verifyChecksum(cls, hrp: str, data: bytes) -> bool:
        checksum = cls._polyMod(cls._hrpExpand(hrp), 1)
        checksum = cls._polyMod(data, checksum)
        return checksum == 1

    @classmethod
    def _convertBits(
            cls,
            data: bytes,
            from_bits: int,
            to_bits: int,
            pad: bool = True) -> Optional[bytes]:
        acc = 0
        bits = 0
        result = []
        max_v = (1 << to_bits) - 1
        max_acc = (1 << (from_bits + to_bits - 1)) - 1

        for value in data:
            if value < 0 or (value >> from_bits):
                return None
            acc = ((acc << from_bits) | value) & max_acc
            bits += from_bits
            while bits >= to_bits:
                bits -= to_bits
                result.append((acc >> bits) & max_v)
        if pad:
            if bits:
                result.append((acc << (to_bits - bits)) & max_v)
        elif bits >= from_bits or ((acc << (to_bits - bits)) & max_v):
            return None
        return bytes(result)

    @classmethod
    def _polyMod(cls, data: bytes, checksum) -> int:
        for v in data:
            checksum0 = checksum >> 25
            checksum = (checksum & 0x1ffffff) << 5 ^ v
            if checksum0 & 1:
                checksum ^= 0x3b6a57b2
            if checksum0 & 2:
                checksum ^= 0x26508e6d
            if checksum0 & 4:
                checksum ^= 0x1ea119fa
            if checksum0 & 8:
                checksum ^= 0x3d4233dd
            if checksum0 & 16:
                checksum ^= 0x2a1462b3
        return checksum
