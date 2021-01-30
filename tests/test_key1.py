import unittest
import logging
from bmnclient.wallet import key as key_mod
from bmnclient.wallet.key import AddressString
from bmnclient.wallet import util  # pylint: disable=E0401,E0611
from bmnclient.wallet import coin_network  # pylint: disable=E0401,E0611
log = logging.getLogger(__name__)


class TestPublicKey(unittest.TestCase):

    def _test_key(self, hex_, is_valid, is_fullyvalid, is_compressed):
        key = key_mod.PublicKey(util.hex_to_bytes(
            hex_), coin_network.BitcoinMainNetwork)
        self.assertEqual(key.is_valid, is_valid)
        self.assertEqual(key.compressed, is_compressed)

    def test_it(self):
        self._test_key('', False, False, False)
        self._test_key('00', False, False, False)

        self._test_key('0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71',
                       True, True, True)
        self._test_key('0478d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71',
                       True, False, True)
        self._test_key('0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71',
                       True, True, True)
        self._test_key('0478d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71a1518063243acd4dfe96b66e3f2ec8013c8e072cd09b3834a19f81f659cc3455',
                       True, True, False)


class Test_primitives(unittest.TestCase):

    def test_addr1(self):
        WIF = 'Kz6UJmQACJmLtaQj5A3JAge4kVTNQ8gbvXuwbmCj7bsaabudb3RD'
        HEX = "55c9bccb9ed68446d1b75273bbce89d7fe013a8acd1625514420fb2aca1a21c4"
        PUBC_HEX = "02157BC6DC9DC7A25D537F36D4714C0CFC11C882F017A989E16956CC1AA8CCE20A"
        # PUB_HEX = "04157BC6DC9DC7A25D537F36D4714C0CFC11C882F017A989E16956CC1AA8CCE20AD64F1B1B8D1C2E38088EAE57F452243E35F7759C13CEA5F0DDD7C496F30DFC62"
        ADDRC = "12Vox8pNW85dFotFrpdAWBM9KN6TuCtX4m"
        # ADDR = "1F2BnPB6j7gB7sdQoSwN7RFDShkWXUmZ4Q"
        prv = key_mod.PrivateKey.from_wif(WIF)
        self.assertEqual(prv.to_hex, HEX)
        self.assertEqual(prv.to_wif, WIF)
        pub = prv.public_key
        self.assertEqual(pub.to_hex.upper(), PUBC_HEX)
        self.assertEqual(pub.to_address(key_mod.AddressType.P2PKH), ADDRC)

    def test_addr2(self):
        WIF = '5KHxtARu5yr1JECrYGEA2YpCPdh1i9ciEgQayAF8kcqApkGzT9s'
        ADDRC = "1ELReFsTCUY2mfaDTy32qxYiT49z786eFg"
        prv = key_mod.PrivateKey.from_wif(WIF)
        # self.assertEqual(prv.to_hex, HEX)
        self.assertEqual(prv.to_wif, WIF)
        pub = prv.public_key
        # self.assertEqual(pub.to_hex.upper(), PUBC_HEX)
        self.assertEqual(pub.to_address(key_mod.AddressType.P2PKH), ADDRC)
