
import unittest
import os
from client.wallet import hd
from client.wallet import key
from client.wallet import coin_network


class Test_address(unittest.TestCase):

    def setUp(self):
        pass

    def test_raw(self):
        GOOD = [
            "MTvnA4CN73ry7c65wEuTSaKzb2pNKHB4n1",
            "3P3QsMVK89JBNqZQv5zMAKG8FK3kJM4rjt",
            "LWxJ1EMDaj4rC8KRyLmvgEiSCNoKjHGZXm",
            "1QGrphsPEbxDFBAz66v1hJJfZXkwu4jcbF",
            "1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX",
        ]
        BAD = [
            "",
            "1O222222222222222222222",
            "00000000000000000",
        ]
        for addr in BAD:
            self.assertFalse(key.AddressString.validate(addr), addr)
        for addr in GOOD:
            self.assertTrue(key.AddressString.validate(addr), addr)

    def test_hd(self):
        seed = os.urandom(32)
        master = hd.HDNode.make_master(
            seed, coin_network.BitcoinMainNetwork)
        for i in range(10):
            child = master.make_child_prv(i, 1 == i % 2)
            self.assertTrue(key.AddressString.validate(
                child.P2PKH), child.P2PKH)
