
import unittest
from client.wallet import coins  # pylint: disable=E0401,E0611


class TestCoins(unittest.TestCase):

    def test_inheritance(self):
        tbtc = coins.BitCoinTest(None)
        btc = coins.BitCoin(None)
        self.assertEqual(tbtc.unit, btc.unit)
        self.assertEqual(tbtc.icon, btc.icon)
