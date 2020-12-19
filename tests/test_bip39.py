
import unittest
import json
from bmnclient.wallet import util
from bmnclient.wallet import hd
from bmnclient.wallet import coin_network
from bmnclient.wallet import mnemonic as mnemo
from bmnclient import gcd, key_manager
from tests import TEST_DATA_PATH


class TestBip39(unittest.TestCase):

    def _test(self, entropy, mnemonic, seed, bip32_xprv, passphrase="TREZOR"):
        calc_seed = mnemo.Mnemonic.to_seed(mnemonic, passphrase)
        self.assertEqual(util.bytes_to_hex(calc_seed), seed,
                         f"entropy: {entropy} seed: {calc_seed}"
                         )
        key_ = hd.HDNode.make_master(
            calc_seed, coin_network.BitcoinMainNetwork)
        self.assertEqual(key_.extended_key, bip32_xprv,
                         f"entropy: {entropy} key: {key_}"
                         )

    def test_english(self):
        body = json.loads(TEST_DATA_PATH.joinpath("bip0039.json").read_text())
        for group in body["english"]:
            self._test(*group)

    @unittest.skip
    def test_jp(self):
        body = json.loads(TEST_DATA_PATH.joinpath(
            "bip0039_jp.json").read_text())
        for group in body:
            self._test(**group)


class TestHighLevel(unittest.TestCase):
    SEED = "advice marble audit eye average vacuum tennis mushroom crowd boil wise roof"

    def _make_adds(self, seed):
        gcd_ = gcd.GCD(True, None)
        km = key_manager.KeyManager(gcd_)
        self.assertTrue(km.generateMasterKey(seed, True))
        for coin in gcd_.all_coins:
            if coin.enabled:
                for _ in range(3):
                    yield coin.make_address().name

    def test_persistency(self):
        one = self._make_adds(self.SEED)
        adds1 = [a for a in one]
        two = self._make_adds(self.SEED)
        adds2 = [a for a in two]
        self.assertEqual(adds1, adds2)
        three = self._make_adds(self.SEED)
        adds3 = [a for a in three]
        self.assertEqual(adds1, adds3)

    def test_variations(self):
        two = self._make_adds(self.SEED + " ")
        adds1 = [a for a in two]
        three = self._make_adds("   " + self.SEED)
        adds2 = [a for a in three]
        self.assertEqual(adds1, adds2)
