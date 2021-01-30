
import unittest
import os
from bmnclient.wallet import hd
from bmnclient.wallet import key
from bmnclient.wallet import coin_network


class TestAddress(unittest.TestCase):
    def test_hd(self):
        seed = os.urandom(32)
        master = hd.HDNode.make_master(
            seed, coin_network.BitcoinMainNetwork)
        for i in range(10):
            child = master.make_child_prv(i, 1 == i % 2)
            self.assertTrue(key.AddressString.validate(
                child.P2PKH), child.P2PKH)
