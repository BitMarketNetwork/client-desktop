import binascii
import hashlib
import unicodedata
from typing import Optional, List

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import bmnclient.version

WORDS_COUNT = 2048
PBKDF2_ROUNDS = 2048
VALID_SEED_LEN = [16, 20, 24, 28, 32]
VALID_MNEMO_LEN = [12, 15, 18, 21, 24]

log = logging.getLogger(__name__)


class WordsSourceError(Exception):
    pass


class Mnemonic:

    def __init__(self, language='english'):
        self.__lang = language
        source_file_path = \
            bmnclient.version.RESOURCES_PATH \
            / "wordlist" \
            / f'{language}.txt'
        with open(source_file_path, 'rt') as fid:
            self.__wordlist = [w.strip() for w in fid.readlines()]
        if len(self.__wordlist) != WORDS_COUNT:
            raise WordsSourceError("Wordlist should contain %d words, but it contains %d words."
                                   % (WORDS_COUNT, len(self.__wordlist)))

    def get_phrase(self, data) -> str:
        if len(data) not in VALID_SEED_LEN:
            raise ValueError(
                f"Data length should be one of the following: {VALID_SEED_LEN}, but it is not {len(data)}.")
        h = hashlib.sha256(data).hexdigest()
        b = (
            bin(int(binascii.hexlify(data), 16))[2:].zfill(len(data) * 8)
            + bin(int(h, 16))[2:].zfill(256)[: len(data) * 8 // 32]
        )
        result = []

        for i in range(len(b) // 11):
            idx = int(b[i * 11: (i + 1) * 11], 2)
            result.append(self._word_list[idx])
        if self._language == "japanese":
            result_phrase = "\u3000".join(result)
        else:
            result_phrase = " ".join(result)
        return result_phrase

    def check_words(self, words: Union[str, list]) -> None:
        """
        Check if these words exist in vocabulary
        """
        if isinstance(words, str):
            words = words.split()
        if len(words) not in VALID_MNEMO_LEN:
            raise ValueError(
                f"Data length should be one of the following: {VALID_MNEMO_LEN}, but it is {len(words)}.")
        if len(words) != len(set(words)):
            raise ValueError( f"Two equal words in passphrase. {len(set(words))}")
        alien = next((w for w in words if w not in self.__wordlist), None)
        if alien:
            raise ValueError(f"Unknown word:{alien}")

    @property
    def wordlist(self) -> List[str]:
        "for debugging purposes"
        return self.__wordlist

    @classmethod
    def toSeed(
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
    def normalizePhrase(cls, string: str) -> str:
        return unicodedata.normalize("NFKD", string)

    @classmethod
    def getLanguageList(cls) -> List[str]:
        result = []
        for f in cls.SOURCE_PATH.iterdir():
            if f.suffix == ".txt" and f.stem:
                result.append(f.stem)
        return result
