import unittest
from bmnclient import gcd
import key_store


class TestHighLevel(unittest.TestCase):
    SEED = "advice marble audit eye average vacuum tennis mushroom crowd boil wise roof"

    def _make_adds(self, seed):
        gcd_ = gcd.GCD(True, None)
        km = key_store.KeyStore(gcd_)
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
