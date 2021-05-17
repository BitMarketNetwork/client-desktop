import hashlib
import logging
import unittest

import ecdsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec

from bmnclient.wallet import coin_network, util

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
