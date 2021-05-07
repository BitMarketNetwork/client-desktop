import enum
import logging
import struct
from typing import Any
import base64
from ..key_store import KeyIndex

log = logging.getLogger(__name__)


class Type(enum.IntEnum):
    TypeText = 1
    TypeBytes = 2
    TypeInt = 3
    TypeBool = 4
    TypeReal = 5


class Cipher:
    ENCRYPT = True

    def __init__(self) -> None:
        from ..application import CoreApplication
        self._cipher = CoreApplication.instance().keyStore.deriveCipher(KeyIndex.WALLET_DATABASE)

    def text_from(self, value: bytes) -> str:
        if self.ENCRYPT:
            return self._decrypt(value)
        return value.decode()

    def _decrypt(self, value: bytes) -> Any:
        try:
            if not value:
                return ""
            # leave it for a while
            if value[0] == 76:
                val = self._cipher.decrypt(None, base64.b64decode(value)[1:])
            elif value[0] == 75:
                val = self._cipher.decrypt(None, base64.b64decode(value)[1:])
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
                return struct.unpack("q", val[1:])[0]
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
                return base64.b64encode(
                    b'+' +
                    self._cipher.encrypt(None, bytes([type_]) + value)).decode()
            else:
                return base64.b64encode(
                    b'-' +
                    self._cipher.encrypt(None, bytes([type_]) + value)).decode()
        except RuntimeError as re:
            log.fatal(f"{re} +> {value}")
        except Exception as te:
            log.fatal(f"{te} ++> {value}")
#

    def encrypt(self, value: Any, strong: bool) -> str:
        if value is None:
            return ""
        if not self.ENCRYPT:
            return value
        try:
            if isinstance(value, str):
                return self._encrypt(value.encode(), Type.TypeText, strong)
            if isinstance(value, bytes):
                return self._encrypt(value, Type.TypeBytes, strong)
            if isinstance(value, bool):
                return self._encrypt(struct.pack("?", value), Type.TypeBool, strong)
            if isinstance(value, int):
                return self._encrypt(struct.pack("q", value), Type.TypeInt, strong)
            if isinstance(value, float):
                return self._encrypt(struct.pack("d", value), Type.TypeReal, strong)
        except struct.error as se:
            log.critical(f"packing error:{se} for {value}")
        raise TypeError(f"{value} => {type(value)}")

    def make_hash(self, value: str) -> str:
        return self._cipher.encrypt(None, value.encode(encoding="utf-8")).hex()
