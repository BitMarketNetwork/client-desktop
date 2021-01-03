import json
import logging
import os
import random
import unittest

from bmnclient import key_store
from bmnclient.wallet.mnemonic import Mnemonic
from tests import TEST_DATA_PATH

log = logging.getLogger(__name__)


class TestMnemonic(unittest.TestCase):
    def _test_seed(self, mnemonic: str, password: str, seed: str) -> None:
        # TODO
        #key_ = hd.HDNode.make_master(
        #    calc_seed, coin_network.BitcoinMainNetwork)
        #self.assertEqual(key_.extended_key, bip32_xprv,
        #                 f"entropy: {entropy} key: {key_}"
        #                 )
        result = Mnemonic.toSeed(mnemonic, password)
        self.assertEqual(result.hex(), seed)

    def test_seed_en(self) -> None:
        test_list = json.loads(
            (TEST_DATA_PATH / "bip-0039.json").read_text(encoding="utf-8"))
        for item in test_list["english"]:
            self._test_seed(item[1], "TREZOR", item[2])

    def test_seed_jp(self) -> None:
        test_list = json.loads(
            (TEST_DATA_PATH / "bip-0039_jp.json").read_text(encoding="utf-8"))
        for item in test_list:
            self._test_seed(item["mnemonic"], item["passphrase"], item["seed"])

    def test_valid(self):
        mnemo = Mnemonic()
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
