

import logging
import os
import unittest
import base64

from client.wallet import aes, sym_encrypt_abc, util
from client.wallet.database import encrypt_proxy

log = logging.getLogger(__name__)


class Test_base(unittest.TestCase):
    BACKEND_CLS = aes.AesProvider
    PASSWORD_GEN = (
        "short",
        "long" * 10,
        b"bytes",
        b"long bytes" * 10,
    )

    def test_encode_decode(self):
        nonce = os.urandom(16)

        def check(psw, body):
            backend = self.BACKEND_CLS(psw, nonce)
            another_backend = self.BACKEND_CLS(psw, nonce)
            enc1 = backend.encode(util.get_bytes(body), True)
            dec1 = another_backend.decode(enc1, True)
            enc2 = backend.encode(util.get_bytes(body), False)
            dec2 = another_backend.decode(enc2, False)
            self.assertEqual(body, dec1)
            self.assertEqual(body, dec2)
            self.assertNotEqual(enc1, enc2)
        for i in range(1, 1001, 100):
            phrase_long = util.get_bytes("aBs_АбЭЮЯұӯ%уeèëpoœm四永工场")
            phrase_short = util.get_bytes("与令@Ё")
            {check(psw, phrase_long * i): check(psw[::-1], phrase_short*i)
                for psw in self.PASSWORD_GEN}


class Test_proxy(unittest.TestCase):

    def test_strong_nonce(self):
        nonce = os.urandom(16)
        psw = os.urandom(32)
        ep = encrypt_proxy.EncryptProxy(psw, nonce)
        seed = os.urandom(64)
        weak = ep.encrypt(seed, False)
        self.assertEqual(seed , ep.text_from(weak.encode()))
        strong = ep.encrypt(seed, True)
        self.assertEqual(seed , ep.text_from(strong.encode()))
        self.assertNotEqual( strong, weak)
        self.assertEqual( len(strong) , len(weak) + 24 )
