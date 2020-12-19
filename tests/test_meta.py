

import unittest
import logging
from bmnclient import gcd
from bmnclient.wallet import coins, address
log = logging.getLogger(__name__)

class TestMeta(unittest.TestCase):

    def test_seq(self):
        gcd_ = gcd.GCD()
        log.debug(gcd_.count(10))
        #
        coin = coins.BitCoin(None)
        coin.add_watch_address("-")
        coin.add_watch_address("--")
        addr = coin.add_watch_address("---")
        coin.add_watch_address("----")
        self.assertEqual(coin.index(addr), 2)
        self.assertEqual(coin.count(addr) , 1)
        #
        def addtx(name):
            tx = addr.make_dummy_tx(addr)
            tx.name = name
            addr.add_tx(tx)
            return tx
        addtx("+")
        tx_ = addtx("+++")
        addtx("++")
        addtx("++++")
        self.assertEqual(addr.count(tx_) , 1)

