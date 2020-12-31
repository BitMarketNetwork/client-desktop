import enum
import logging
import struct
from typing import Any
import base64
from ...root_key import KeyType

log = logging.getLogger(__name__)


class Type(enum.IntEnum):
    TypeText = 1
    TypeBytes = 2
    TypeInt = 3
    TypeBool = 4
    TypeReal = 5


class EncryptProxy:
    ENCRYPT = True

    def __init__(self, psw, nonce):
        self._last_hash = None
        self._cipher = aes.AesProvider( psw, nonce)
        self._password = util.get_bytes(psw)

    def text_from(self, value: bytes) -> str:
        if self.ENCRYPT:
            return self._decrypt(value)
        return value.decode()

    def _decrypt(self, value: bytes) -> Any:
        try:
            if not value:
                return None
            # leave it for a while
            if value[0] == 76:
                val = self._cipher.decode(base64.b64decode(value)[1:], False)
            elif value[0] == 75:
                val = self._cipher.decode(base64.b64decode(value)[1:], True)
            else:
                return int(value)
            pref = val[0]
            if Type.TypeText == pref:
                return val[1:].decode()
            if Type.TypeBytes == pref:
                return val[1:]
            if Type.TypeBool == pref:
                return struct.unpack("?", val[1:])[0]
            if Type.TypeInt == pref:
                return struct.unpack("Q", val[1:])[0]
            if Type.TypeReal == pref:
                return struct.unpack("d", val[1:])[0]
            raise RuntimeError(f"Not implemented type {val}")
        except RuntimeError as re:
            log.fatal(f"{re} +> {value}")
        except Exception as te:
            log.fatal(f"{te} ++> {value}")

    def _encrypt(self, value: Any, type_: Type, strong: bool) -> str:
        try:
            if strong:
                return base64.b64encode(b'+' +
                    self._cipher.encode( bytes([type_]) + value , True)).decode()
            else:
                return base64.b64encode(b'-' +
                    self._cipher.encode( bytes([type_]) + value , False)).decode()
        except RuntimeError as re:
            log.fatal(f"{re} +> {value}")
        except Exception as te:
            log.fatal(f"{te} ++> {value}")
#

    def encrypt(self, value: Any, strong: bool) -> str:
        if not self.ENCRYPT:
            return value
        if value is None:
            return ""
        try:
            if isinstance(value, str):
                return self._encrypt(value.encode(), Type.TypeText, strong)
            if isinstance(value, bytes):
                return self._encrypt(value, Type.TypeBytes, strong)
            if isinstance(value, bool):
                return self._encrypt(struct.pack("?", value), Type.TypeBool, strong)
            if isinstance(value, int):
                return self._encrypt(struct.pack("Q", value), Type.TypeInt, strong)
            if isinstance(value, float):
                return self._encrypt(struct.pack("d", value), Type.TypeReal, strong)
        except struct.error as se:
            log.critical(f"packing error:{se} for {value}")
        raise TypeError(f"{value} => {type(value)}")

    def make_hash(self, value: str) -> str:
        assert self._password
        return blake2b(util.get_bytes(value), key=self._password, digest_size=16).hexdigest()
