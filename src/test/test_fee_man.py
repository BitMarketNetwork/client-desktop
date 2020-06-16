
import unittest
import random
from client.wallet import fee_manager


class Test_FeeManager(unittest.TestCase):

    def test_calculation(self):
        fm = fee_manager.FeeManager(None, {})
        for i in range(10, 100, 10):
            fm.add_fee(i, i*i)

        def check(spb, min): return self.assertEqual(
            fm.get_minutes(spb), min, f"spb: {spb} min:{min} ==> {fm.time_table}")
        check(5, 50)
        check(15, 250)
        check(20, 400)
        check(21, 450)
