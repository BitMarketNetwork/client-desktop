
import hashlib
import logging
import unittest

import ecdsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
import time

from bmnclient.wallet import coin_network, key, util

log = logging.getLogger(__name__)

"""

THIS FILE ISN'T SUPPOSED TO BE INCLUDED IN PRODUCTION TESTS !!!!

get-rid of it as your get up on cryptography

"""

CURVE = ec.SECP256K1()


def pub_to_bytes(pub: ec.EllipticCurvePublicKey, compressed: bool = True) -> bytes:
    assert isinstance(pub, ec.EllipticCurvePublicKey)
    return pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint if compressed else serialization.PublicFormat.UncompressedPoint,
    )


@unittest.skip
class TestBase(unittest.TestCase):

    def test_set(self):
        # from btc-core data
        WIF = "Kz6UJmQACJmLtaQj5A3JAge4kVTNQ8gbvXuwbmCj7bsaabudb3RD"
        HEX = "55c9bccb9ed68446d1b75273bbce89d7fe013a8acd1625514420fb2aca1a21c4"
        PUB_C = "02157BC6DC9DC7A25D537F36D4714C0CFC11C882F017A989E16956CC1AA8CCE20A"
        # BTC main net
        net = coin_network.BitcoinMainNetwork
        data = util.b58_check_decode(WIF)
        self.assertEqual(
            coin_network.CoinNetworkBase.from_prv_version(data[:1]), net)
        self.assertEqual(len(WIF), 52)
        self.assertEqual(data[-1], 1)
        log.warning(f"prv raw: {data}")
        prv_data = util.bytes_to_number(data[1:-1])
        prv = ec.derive_private_key(prv_data, CURVE, default_backend())
        pub = prv.public_key()

        pubhex = pub_to_bytes(pub).hex().upper()
        self.assertEqual(pubhex, PUB_C)
        # !! gotcha !!

        data = b"running wild"
        sig_meth = ec.ECDSA(hashes.SHA256())
        signature = prv.sign(data, sig_meth)
        log.warning(f"sig: {signature}")
        pub.verify(signature, data, sig_meth)

        self.assertEqual(0x100, prv.key_size)
        numbers = prv.private_numbers()
        log.warning(f"prv num: {numbers.private_value}")
        phex = util.number_to_bytes(numbers.private_value, 32).hex()
        log.warning(f"prv str: {phex}")
        self.assertEqual(phex, HEX)
        # !! gotcha !!

    def test_raw_pub(self):
        prv = ec.derive_private_key(
            util.bytes_to_number(bytes.fromhex(
                "18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725")),
            CURVE, default_backend())
        pub = prv.public_key()
        pubhex = pub_to_bytes(pub).hex()
        self.assertEqual(
            pubhex, "0250863ad64a87ae8a2fe83c1af1a8403cb53f53e486d8511dad8a04887e5b2352")
        # !! gotcha !!

    def __test_pub(self, WIF, ADDR, NET, PUB=None):
        # from tests: LTC main net
        data = util.b58_check_decode(WIF)
        log.info(f"wif len: {len(WIF)}  byte:{data[-1]}")
        if 52 == len(WIF) and data[-1] == 1:
            data, comp = data[1:-1], True
        else:
            data, comp = data[1:], False
        prv = ec.derive_private_key(util.bytes_to_number(
            data), CURVE, default_backend())
        pub = prv.public_key()
        num = pub.public_numbers()
        if comp:
            pbs = '02' if 0 == num.y % 2 else '03'
            pbs += '%064x' % num.x
        else:
            pbs = '04' + '%064x' % num.x + '%064x' % num.y
        log.warning(f"pub: {pbs}")
        self.assertEqual(33 << 1 if comp else 65 << 1, len(pbs))
        pbs_data1 = util.hex_to_bytes(pbs)
        pbs_data2 = pub_to_bytes(pub, comp)
        self.assertEqual(33 if comp else 65, len(pbs_data1))
        self.assertEqual(pbs_data1, pbs_data2)
        if PUB:
            self.assertEqual(PUB, pbs_data2.hex().upper())
        addr = util.b58_check_encode(NET.ADDRESS_BYTE_PREFIX +
                                     util.hash160(pbs_data2))
        log.warning(f"addr: {addr}")
        self.assertEqual(ADDR, addr)

    def test_pub_ltc1(self):
        WIF = 'TAwazXNuGfE4U3hVMLgAtgzw6tZu2sNF8igweoESTDBEfrnh1Jo4'
        ADDR = 'LWFvvfLCSpdSXzXgb6wUfwkfv6QDipAzJc'
        NET = coin_network.LitecoinMainNetwork
        self.__test_pub(
            WIF, ADDR, NET, PUB="03AD1D8E89212F0B92C74D23BB710C00662AD1470198AC48C43F7D6F93A2A26873")

    def test_pub_ltc2(self):
        WIF = '6ut8HoyTgiG12tfroAo6SQnquArWUi4z9wa7BPyRZnvFSANot6o'
        ADDR = 'LVqZnxtoDXGZ7qW9rHxkp1twhJC1TYgUkQ'
        NET = coin_network.LitecoinMainNetwork
        self.__test_pub(WIF, ADDR, NET)

    def test_pub_btc(self):
        WIF = 'L3jsepcttyuJK3HKezD4qqRKGtwc8d2d1Nw6vsoPDX9cMcUxqqMv'
        ADDR = '1ExJJsNLQDNVVM1s1sdyt1o5P3GC5r32UG'
        NET = coin_network.BitcoinMainNetwork
        self.__test_pub(WIF, ADDR, NET)
        # !! gotcha !!


@unittest.skip
class TestSignature(unittest.TestCase):

    # u should use raw pyca implementation before using teest
    @unittest.skip
    def test_S(self):
        WIF = "Kz6UJmQACJmLtaQj5A3JAge4kVTNQ8gbvXuwbmCj7bsaabudb3RD"
        # BTC main net
        prv = key.PrivateKey.from_wif(WIF)
        ec_prv = ecdsa.SigningKey.from_string(
            bytes.fromhex(prv.to_hex),
            curve=ecdsa.SECP256k1,
            hashfunc=hashlib.sha256,
        )
        message = "what the fuck" * 100
        message_hash = util.sha256(message)
        pyc_signed = prv.sign(message)
        ec_signed = ec_prv.sign(message_hash)
        pub = prv.public_key
        ec_pub = ec_prv.verifying_key
        # all is good
        self.assertEqual(prv.to_hex, ec_prv.to_string().hex())
        self.assertEqual(pub.to_hex, ec_pub.to_string("compressed").hex())
        self.assertTrue(prv.verify(pyc_signed, message))
        self.assertTrue(ec_pub.verify(ec_signed, message_hash))
        # but
        self.assertEqual(pyc_signed, ec_signed)
