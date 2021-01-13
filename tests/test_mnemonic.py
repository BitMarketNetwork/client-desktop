# JOK+
import json
import os
import random
import unittest

from bmnclient.wallet.mnemonic import Mnemonic
from bmnclient.wallet.hd import HDNode
from tests import TEST_DATA_PATH, getLogger

_logger = getLogger(__name__)


class TestMnemonic(unittest.TestCase):
    def _test_seed(
            self,
            language: str,
            entropy: str,
            phrase: str,
            password: str,
            seed: str,
            bip32_xprv: str) -> None:
        mnemonic = Mnemonic(language)
        generated_phrase = mnemonic.getPhrase(bytes.fromhex(entropy))
        self.assertEqual(
            Mnemonic.normalizePhrase(generated_phrase),
            Mnemonic.normalizePhrase(phrase))

        self.assertTrue(mnemonic.isValidPhrase(generated_phrase))
        self.assertTrue(mnemonic.isValidPhrase(phrase))

        generated_seed = Mnemonic.phraseToSeed(phrase, password)
        self.assertEqual(generated_seed.hex(), seed)

        # TODO
        hd_node = HDNode.make_master(generated_seed)
        from bmnclient.wallet.coin_network import BitcoinMainNetwork
        hd_node.key._network = BitcoinMainNetwork
        self.assertEqual(bip32_xprv, hd_node.extended_key)

    def test_seed_en(self) -> None:
        test_list = json.loads(
            (TEST_DATA_PATH / "bip-0039.json").read_text(encoding="utf-8"))
        for item in test_list["english"]:
            self._test_seed(
                "english",
                item[0],
                item[1],
                "TREZOR",
                item[2],
                item[3])

    def test_seed_jp(self) -> None:
        test_list = json.loads(
            (TEST_DATA_PATH / "bip-0039_jp.json").read_text(encoding="utf-8"))
        for item in test_list:
            self._test_seed(
                "japanese",
                item["entropy"],
                item["mnemonic"],
                item["passphrase"],
                item["seed"],
                item["bip32_xprv"])

    def test_valid(self) -> None:
        for language in Mnemonic.getLanguageList():
            mnemonic = Mnemonic(language)
            for i in range(2000):
                phrase = mnemonic.getPhrase(
                    os.urandom(random.choice(Mnemonic.DATA_LENGTH_LIST)))
                if i == 1:
                    _logger.debug("Random phrase {}: {}".format(i, phrase))
                self.assertTrue(mnemonic.isValidPhrase(phrase))
                self.assertFalse(mnemonic.isValidPhrase(
                    phrase + " " + random.choice(mnemonic._word_list)))
