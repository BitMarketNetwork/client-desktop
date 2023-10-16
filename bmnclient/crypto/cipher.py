from __future__ import annotations

import os
from enum import Enum, auto
from typing import TYPE_CHECKING

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import ciphers
from cryptography.hazmat.primitives.ciphers import aead, algorithms, modes

from ..utils.class_property import classproperty
from ..version import Product

if TYPE_CHECKING:
    from typing import Any, Final, Optional, Type


class AbstractCipher:
    _KEY_SIZE: int = 0

    class OpMode(Enum):
        ENCRYPT = auto()
        DECRYPT = auto()

    def __init__(self, op_mode: OpMode, context: Any) -> None:
        if op_mode not in self.OpMode:
            raise ValueError("unknown op mode '{}'".format(str(op_mode)))
        self._op_mode = op_mode
        self._context = context

    @classmethod
    def generateKey(cls) -> bytes:
        return os.urandom(cls._KEY_SIZE * 8)

    def update(self, data: bytes) -> bytes:
        raise NotImplementedError

    def finalize(self) -> bytes:
        raise NotImplementedError


class AbstractHazmatCipher(AbstractCipher):
    _HAZMAT_ALGORITHM: Optional[Type[ciphers.CipherAlgorithm]] = None
    _HAZMAT_MODE: Optional[Type[modes.Mode]] = None

    def __init__(
        self,
        op_mode: AbstractHazmatCipher.OpMode,
        key: bytes,
        mode_arg: bytes,
        context: Optional[ciphers.CipherContext] = None,
    ) -> None:
        if not context:
            # noinspection PyArgumentList
            context = ciphers.Cipher(
                self._HAZMAT_ALGORITHM(key), self._HAZMAT_MODE(mode_arg)
            )
            if op_mode == self.OpMode.ENCRYPT:
                context = context.encryptor()
            else:  # if op_mode == self.OpMode.DECRYPT:
                context = context.decryptor()
        super().__init__(op_mode, context)

    def update(self, data: bytes) -> bytes:
        return self._context.update(data)

    def finalize(self) -> bytes:
        return self._context.finalize()


class BlockDeviceCipher(AbstractHazmatCipher):
    _HAZMAT_ALGORITHM: Final = algorithms.AES
    _HAZMAT_MODE: Final = modes.XTS
    _KEY_SIZE: Final = (256 // 8) * 2
    _SALT_SIZE: Final = 16 - 4

    def __init__(
        self,
        op_mode: BlockDeviceCipher.OpMode,
        key: bytes,
        sector_index: int,
        salt: bytes,
    ) -> None:
        if len(salt) != self._SALT_SIZE:
            raise ValueError("salt must be {} bytes".format(self._SALT_SIZE))
        super().__init__(
            op_mode, key, sector_index.to_bytes(4, "little") + salt
        )

    @classproperty
    def saltSize(cls) -> int:  # noqa
        return cls._SALT_SIZE


# TODO reimplement
class AeadCipher:
    _CIPHER: Final = aead.AESGCM
    _NONCE_SIZE: Final = 96 // 8  # NIST recommends
    _KEY_SIZE: Final = 128 // 8
    _ASSOCIATED_DATA: Final = Product.SHORT_NAME.encode()

    def __init__(self, key: bytes, nonce: Optional[bytes] = None) -> None:
        self._cipher = self._CIPHER(key)
        self._nonce = nonce

    @classmethod
    def generateNonce(cls) -> bytes:
        return os.urandom(cls._NONCE_SIZE)

    @classmethod
    def generateKey(cls) -> bytes:
        return cls._CIPHER.generate_key(cls._KEY_SIZE * 8)

    def encrypt(self, nonce: Optional[bytes], data: bytes) -> bytes:
        return self._cipher.encrypt(
            nonce or self._nonce, data, self._ASSOCIATED_DATA
        )

    def decrypt(self, nonce: Optional[bytes], data: bytes) -> Optional[bytes]:
        try:
            return self._cipher.decrypt(
                nonce or self._nonce, data, self._ASSOCIATED_DATA
            )
        except InvalidTag:
            return None


class MessageCipher(AeadCipher):
    def __init(self, key: bytes) -> None:
        super().__init__(key, None)

    def encrypt(
        self, data: bytes, separator: str = Product.STRING_SEPARATOR
    ) -> str:
        nonce = self.generateNonce()
        cipher_text = super().encrypt(nonce, data)
        return nonce.hex() + separator + cipher_text.hex()

    def decrypt(
        self, text: str, separator: str = Product.STRING_SEPARATOR
    ) -> Optional[bytes]:
        try:
            (nonce, data) = text.split(separator, 1)
            return super().decrypt(bytes.fromhex(nonce), bytes.fromhex(data))
        except (ValueError, TypeError):
            return None
