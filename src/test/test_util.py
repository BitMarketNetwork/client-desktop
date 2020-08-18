
import unittest
import os
from client.wallet import util


class TestUtil(unittest.TestCase):

    def test_hex(self):
        bytes = os.urandom(64)
        hex = util.bytes_to_hex(bytes)
        self.assertEqual(bytes, util.hex_to_bytes(hex))

    def test_b58(self):
        bytes_ = os.urandom(64)
        self.assertEqual(bytes_, util.b58_decode(util.b58_encode(bytes_)))
        b58check = util.b58_check_encode(bytes_)
        self.assertTrue(util.b58_check_validate(b58check))
        self.assertTrue(bytes_, util.b58_check_decode(b58check))
