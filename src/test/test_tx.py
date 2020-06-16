
import unittest
import logging
from client.wallet import tx
from client.wallet import address
from client.wallet import coins
log = logging.getLogger(__name__)


class Test_Tx_process(unittest.TestCase):

    def test_direction(self):
        coin = coins.BitCoin(None)
        addr = address.CAddress("123", coin)
        trx = tx.Transaction(addr)
        addr.add_tx(trx)
