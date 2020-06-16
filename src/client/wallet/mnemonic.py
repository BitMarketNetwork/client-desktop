
import binascii
import hashlib
from importlib import resources
from typing import Union

from . import util

WORDS_COUNT = 2048
PBKDF2_ROUNDS = 2048


class WordsSourceError(Exception):
    pass


class Mnemonic:

    def __init__(self, language='english'):
        self._lang = language
        from . import wordlist
        with resources.open_text(wordlist, f'{language}.txt') as fid:
            self._wordlist = [w.strip() for w in fid.readlines()]
        if len(self._wordlist) != WORDS_COUNT:
            raise WordsSourceError("Wordlist should contain %d words, but it contains %d words."
                                   % (WORDS_COUNT, len(self._wordlist)))

    def get_phrase(self, data):
        if len(data) not in [16, 20, 24, 28, 32]:
            raise ValueError(
                "Data length should be one of the following: [16, 20, 24, 28, 32], but it is not (%d)."
                % len(data)
            )
        h = hashlib.sha256(data).hexdigest()
        b = (
            bin(int(binascii.hexlify(data), 16))[2:].zfill(len(data) * 8)
            + bin(int(h, 16))[2:].zfill(256)[: len(data) * 8 // 32]
        )
        result = []
        for i in range(len(b) // 11):
            idx = int(b[i * 11: (i + 1) * 11], 2)
            result.append(self._wordlist[idx])
        if self._lang == "japanese":
            result_phrase = u"\u3000".join(result)
        else:
            result_phrase = " ".join(result)
        return result_phrase

    def check_words(self, words):
        """
        Check if these words exist in vocabulary
        """
        if isinstance(words, str):
            words = words.split()
        if len(words) not in [16, 20, 24, 28, 32]:
            raise ValueError(
                "Data length should be one of the following: [16, 20, 24, 28, 32], but it is not (%d)."
                % len(words)
            )
        aliens = (w for w in words if w not in self._wordlist)
        if aliens:
            raise ValueError(f"Unknown word:{next(aliens)}")

    @classmethod
    def to_seed(cls, mnemonic: Union[str, bytes], passphrase: str) -> bytes:
        passphrase = "mnemonic" + util.normalize_string(passphrase)
        stretched = hashlib.pbkdf2_hmac("sha512", util.normalize_string(
            mnemonic).encode(), passphrase.encode(), PBKDF2_ROUNDS)
        return stretched[:64]
