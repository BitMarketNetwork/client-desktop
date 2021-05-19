# JOK4
from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..crypto.digest import Sha256Digest
from ..logger import Logger
from ..utils.class_property import classproperty
from ..version import ProductPaths

if TYPE_CHECKING:
    from typing import Final, List, Optional, Sequence, Union


# Adapted from:
# https://github.com/trezor/python-mnemonic/blob/faa9c607d9a4b4fb1e2b2bc79a341a60181e3381/mnemonic/mnemonic.py
class Mnemonic:
    _ENCODING: Final = "utf-8"
    _WORD_COUNT: Final = 2048
    _SOURCE_PATH: Final = ProductPaths.RESOURCES_PATH / "wordlist"
    _PBKDF2_ROUNDS: Final = 2048

    _DATA_LENGTH_LIST: Final = (16, 20, 24, 28, 32)
    _DEFAULT_DATA_LENGTH: Final = 24
    _PHRASE_WORD_COUNT_LIST: Final = (12, 15, 18, 21, 24)

    def __init__(self, language: Optional[str] = None) -> None:
        self._language = language.lower() if language else "english"
        self._logger = Logger.getClassLogger(
            __name__,
            self.__class__,
            self._language)
        self._file_path = self._SOURCE_PATH / (self._language + ".txt")

        error_message = None
        try:
            self._logger.debug("Reading words from '%s'...", self._file_path)
            with open(  # TODO global cache
                    self._file_path,
                    mode="rt",
                    encoding=self._ENCODING,
                    errors="strict") as file:
                self._word_list = [word.strip() for word in file.readlines()]
            if len(self._word_list) != self._WORD_COUNT:
                raise ValueError(
                    "wordlist should contain {} words, but it contains {} words"
                    .format(self._WORD_COUNT, len(self._word_list)))
        except OSError as e:
            error_message = Logger.osErrorToString(e)
        except ValueError as e:
            error_message = Logger.exceptionToString(e)
        if error_message is not None:
            Logger.fatal(
                "Failed to read file '{}'. {}"
                .format(self._file_path, error_message),
                self._logger)

    @classproperty
    def dataLengthList(cls) -> Sequence:  # noqa
        return cls._DATA_LENGTH_LIST

    @classproperty
    def defaultDataLength(cls) -> int:  # noqa
        return cls._DEFAULT_DATA_LENGTH

    @property
    def language(self) -> str:
        return self._language

    def getPhrase(self, data: bytes) -> str:
        if len(data) not in self._DATA_LENGTH_LIST:
            Logger.fatal(
                "Data length should be one of the following: {}, but data "
                "length {}."
                .format(self._DATA_LENGTH_LIST, len(data)),
                self._logger)

        h = Sha256Digest().update(data).finalize().hex()

        b = bin(int.from_bytes(data, byteorder="big"))[2:].zfill(len(data) * 8)
        b += bin(int(h, 16))[2:].zfill(256)[: len(data) * 8 // 32]
        result = []

        for i in range(len(b) // 11):
            i = int(b[i * 11: (i + 1) * 11], 2)
            result.append(self._word_list[i])
        return self.friendlyPhrase(self._language, result)

    def isValidPhrase(self, phrase: str) -> bool:
        phrase = self.normalizePhrase(phrase).split()
        if len(phrase) not in self._PHRASE_WORD_COUNT_LIST:
            return False
        try:
            b = map(
                lambda x: bin(self._word_list.index(x))[2:].zfill(11),
                phrase)
            b = "".join(b)

            j = len(b)
            d = b[: j // 33 * 32]
            h = b[-j // 33:]
            nd = int(d, 2).to_bytes(j // 33 * 4, "big")
        except (ValueError, OverflowError):
            return False

        nh = Sha256Digest().update(nd).finalize().hex()
        nh = bin(int(nh, 16))[2:].zfill(256)[: j // 33]
        return h == nh

    @classmethod
    def phraseToSeed(
            cls,
            phrase: str,
            password: Optional[str] = None) -> bytes:
        phrase = cls.normalizePhrase(phrase)
        if password is None:
            password = "".join(phrase[::-3])
        else:
            password = cls.normalizePhrase(password)

        password = ("mnemonic" + password).encode(cls._ENCODING)
        phrase = phrase.encode(cls._ENCODING)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=64,
            salt=password,
            iterations=cls._PBKDF2_ROUNDS)
        seed = kdf.derive(phrase)
        assert len(seed) == 64
        return seed

    @classmethod
    def isEqualPhrases(cls, phrase1: str, phrase2: str) -> bool:
        if len(phrase1) <= 0 or len(phrase2) <= 0:
            return False
        phrase1 = Mnemonic.normalizePhrase(phrase1)
        phrase2 = Mnemonic.normalizePhrase(phrase2)
        return phrase1 == phrase2

    @classmethod
    def normalizePhrase(cls, phrase: str) -> str:
        return unicodedata.normalize("NFKD", phrase).strip()

    @classmethod
    def friendlyPhrase(
            cls,
            language: str,
            phrase: Union[str, Sequence[str]]) -> str:
        if isinstance(phrase, str):
            phrase = cls.normalizePhrase(phrase).split()
            # phrase = filter(None, phrase)
        if language == "japanese":
            phrase = "\u3000".join(phrase)
        else:
            phrase = " ".join(phrase)
        return phrase

    @classmethod
    def getLanguageList(cls) -> List[str]:
        result = []
        for f in cls._SOURCE_PATH.iterdir():
            if f.suffix == ".txt" and f.stem:
                result.append(f.stem)
        return result
