

import logging
import unittest
import os
import random
import key_store
from bmnclient.wallet import mnemonic


log = logging.getLogger(__name__)


class TestMnemo(unittest.TestCase):

    def test_valid(self):
        mnemo = mnemonic.Mnemonic()
        for i in range(100):
            phr = mnemo.get_phrase(os.urandom(key_store.MNEMONIC_SEED_LENGTH))
            log.warning(f"{i}: {phr}")
            mnemo.check_words(phr)
        #
        split = phr.split()
        last = split[-1]
        wrong_phr = phr.replace(last, last.upper())
        with self.assertRaises(ValueError):
            mnemo.check_words(wrong_phr)
        wrong_phr = phr.replace(last, last.upper())
        with self.assertRaises(ValueError):
            mnemo.check_words(wrong_phr)
        wrong_phr = phr.replace(last, split[0])
        with self.assertRaises(ValueError):
            mnemo.check_words(wrong_phr)
        new_word = random.choice(mnemo.wordlist)
        wrong_phr = " ".join(split + [new_word])
        with self.assertRaises(ValueError):
            mnemo.check_words(wrong_phr)
