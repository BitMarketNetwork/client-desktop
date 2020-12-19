from typing import List
import binascii
import hashlib
import logging
from typing import Union, Optional
import bmnclient.version
from . import util

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
            log.error(idx)
            result.append(self.__wordlist[idx])
        if self.__lang == "japanese":
            result_phrase = u"\u3000".join(result)
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
    def to_seed(cls, mnemonic: Union[str, bytes], passphrase: Optional[str] = None) -> bytes:
        if passphrase is None:
            passphrase = "".join(mnemonic[::-3])
        passphrase = "mnemonic" + util.normalize_string(passphrase)
        # log.warning(f"seed salt: {passphrase} ({len(passphrase)})")
        stretched = hashlib.pbkdf2_hmac("sha512", util.normalize_string(
            mnemonic).encode(), passphrase.encode(), PBKDF2_ROUNDS)
        return stretched[:64]
