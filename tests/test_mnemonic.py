# JOK4
import json
import os
import random
from unittest import TestCase

from bmnclient.coins.coin_bitcoin import Bitcoin
from bmnclient.coins.hd import HdNode
from bmnclient.coins.mnemonic import Mnemonic
from tests import getLogger, TEST_DATA_PATH

_logger = getLogger(__name__)


class TestMnemonic(TestCase):
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

        root_node = HdNode.deriveRootNode(generated_seed)
        self.assertIsNotNone(root_node)
        self.assertEqual(bip32_xprv, root_node.toExtendedKey(
            Bitcoin.bip0032VersionPrivateKey,
            private=True))

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
                    os.urandom(random.choice(Mnemonic.dataLengthList)))
                if i == 1:
                    _logger.debug("Random phrase {}: {}".format(i, phrase))
                self.assertTrue(mnemonic.isValidPhrase(phrase))
                # noinspection PyProtectedMember
                self.assertFalse(mnemonic.isValidPhrase(
                    phrase + " " + random.choice(mnemonic._word_list)))
