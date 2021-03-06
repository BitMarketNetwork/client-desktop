
import unittest
from bmnclient.wallet import coins  # pylint: disable=E0401,E0611


class TestCoins(unittest.TestCase):

    def test_inheritance(self):
        tbtc = coins.BitcoinTest(None)
        btc = coins.Bitcoin(None)
        self.assertEqual(tbtc.unit, btc.unit)
        self.assertEqual(tbtc.icon, btc.icon)
