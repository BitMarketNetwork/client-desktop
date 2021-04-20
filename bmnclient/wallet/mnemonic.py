# JOK+
import unicodedata
from typing import Optional, List, Union, Iterable

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..crypto.digest import Sha256Digest
from ..version import ProductPaths


# Adapted from:
# https://github.com/trezor/python-mnemonic/blob/faa9c607d9a4b4fb1e2b2bc79a341a60181e3381/mnemonic/mnemonic.py
class Mnemonic:
    ENCODING = "utf-8"
    WORD_COUNT = 2048
    SOURCE_PATH = ProductPaths.RESOURCES_PATH / "wordlist"
    PBKDF2_ROUNDS = 2048

    DATA_LENGTH_LIST = (16, 20, 24, 28, 32)
    DEFAULT_DATA_LENGTH = 24
    PHRASE_WORD_COUNT_LIST = (12, 15, 18, 21, 24)

    def __init__(self, language: str = None) -> None:
        self._language = language.lower() if language else "english"
        with open(  # TODO global cache
                self.SOURCE_PATH / (self._language + ".txt"),
                mode="rt",
                encoding=self.ENCODING) as file:
            self._word_list = [word.strip() for word in file.readlines()]
        if len(self._word_list) != self.WORD_COUNT:
            raise RuntimeError(
                "wordlist should contain {} words, but it contains {} words"
                .format(self.WORD_COUNT, len(self._word_list)))

    @property
    def language(self) -> str:
        return self._language

    def getPhrase(self, data: bytes) -> str:
        if len(data) not in self.DATA_LENGTH_LIST:
            raise ValueError(
                "data length should be one of the following: {}, "
                "but data length {}"
                .format(self.DATA_LENGTH_LIST, len(data)))
        h = Sha256Digest()
        h.update(data)
        h = h.final().hex()

        b = bin(int.from_bytes(data, byteorder="big"))[2:].zfill(len(data) * 8)
        b += bin(int(h, 16))[2:].zfill(256)[: len(data) * 8 // 32]
        result = []

        for i in range(len(b) // 11):
            i = int(b[i * 11: (i + 1) * 11], 2)
            result.append(self._word_list[i])
        return self.friendlyPhrase(self._language, result)

    def isValidPhrase(self, phrase: str) -> bool:
        phrase = self.normalizePhrase(phrase).split()
        if len(phrase) not in self.PHRASE_WORD_COUNT_LIST:
            return False
        try:
            b = map(
                lambda x: bin(self._word_list.index(x))[2:].zfill(11),
                phrase)
            b = "".join(b)
        except ValueError:
            return False
        j = len(b)
        d = b[: j // 33 * 32]
        h = b[-j // 33:]
        nd = int(d, 2).to_bytes(j // 33 * 4, byteorder="big")

        nh = Sha256Digest()
        nh.update(nd)
        nh = nh.final().hex()
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

        password = ("mnemonic" + password).encode(cls.ENCODING)
        phrase = phrase.encode(cls.ENCODING)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=64,
            salt=password,
            iterations=cls.PBKDF2_ROUNDS)
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
            phrase: Union[str, Iterable[str]]) -> str:
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
        for f in cls.SOURCE_PATH.iterdir():
            if f.suffix == ".txt" and f.stem:
                result.append(f.stem)
        return result
