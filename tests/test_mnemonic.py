# JOK+
import json
import os
import random
import unittest

from bmnclient.wallet.mnemonic import Mnemonic
from tests import TEST_DATA_PATH, getLogger

_logger = getLogger(__name__)


class TestMnemonic(unittest.TestCase):
    def _test_seed(
            self,
            language: str,
            entropy: str,
            phrase: str,
            password: str,
            seed: str) -> None:
        # TODO
        #key_ = hd.HDNode.make_master(
        #    calc_seed, coin_network.BitcoinMainNetwork)
        #self.assertEqual(key_.extended_key, bip32_xprv,
        #                 f"entropy: {entropy} key: {key_}"
        #                 )

        mnemonic = Mnemonic(language)
        generated_phrase = mnemonic.getPhrase(bytes.fromhex(entropy))
        self.assertEqual(
            Mnemonic.normalizePhrase(generated_phrase),
            Mnemonic.normalizePhrase(phrase))

        self.assertTrue(mnemonic.isValid(generated_phrase))
        self.assertTrue(mnemonic.isValid(phrase))

        self.assertEqual(Mnemonic.toSeed(phrase, password).hex(), seed)

    def test_seed_en(self) -> None:
        test_list = json.loads(
            (TEST_DATA_PATH / "bip-0039.json").read_text(encoding="utf-8"))
        for item in test_list["english"]:
            self._test_seed(
                "english",
                item[0],
                item[1],
                "TREZOR",
                item[2])

    def test_seed_jp(self) -> None:
        test_list = json.loads(
            (TEST_DATA_PATH / "bip-0039_jp.json").read_text(encoding="utf-8"))
        for item in test_list:
            self._test_seed(
                "japanese",
                item["entropy"],
                item["mnemonic"],
                item["passphrase"],
                item["seed"])

    def test_valid(self) -> None:
        for language in Mnemonic.getLanguageList():
            mnemonic = Mnemonic(language)
            for i in range(1000):
                phrase = mnemonic.getPhrase(
                    os.urandom(random.choice(Mnemonic.DATA_LENGTH_LIST)))
                if i == 1:
                    _logger.debug("Random phrase {}: {}".format(i, phrase))
                self.assertTrue(mnemonic.isValid(phrase))
                self.assertFalse(mnemonic.isValid(
                    phrase + " " + random.choice(mnemonic._word_list)))
