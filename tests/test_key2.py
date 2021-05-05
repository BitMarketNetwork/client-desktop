
import json
import logging
import os
import random
import unittest

from bmnclient.wallet import coin_network, hd, key, key_format, mtx_impl as \
    mtx, \
    util
from tests import TEST_DATA_PATH
from tests.test_data import *

log = logging.getLogger(__name__)

UNSPENTS = [
    # For BITCOIN_WALLET_MAIN/TEST:
    mtx.UTXO(100000000,
             1,
             '76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac',
             'f09c22717770fcd7e477953c3ca7ecb9bd44ec4d5392f24fdd247dbb8db2d388',
             0,
             'p2pkh'),
    # For BITCOIN_WALLET_COMPRESSED_MAIN/TEST:
    mtx.UTXO(100000000,
             1,
             '76a914990ef60d63b5b5964a1c2282061af45123e93fcb88ac',
             'f09c22717770fcd7e477953c3ca7ecb9bd44ec4d5392f24fdd247dbb8db2d388',
             0,
             'p2pkh'),
    mtx.UTXO(100000000,
             1,
             '0014990ef60d63b5b5964a1c2282061af45123e93fcb',
             'f42c4ee1f95a3c9f5b1c6db356b72cd655fdb5de30c45fc148d3d86016b4d4cb',
             0,
             'np2wkh'),
    # For MultiSig of WALLET_FORMAT_MAIN_1/2:
    mtx.UTXO(2000000000,
             1,
             'a914d28919b55811c8ffb40b23092298843f82994a7c87',
             '64064449fc2aab13316e90beb6c2a224d86a08733ff5b48e422be7688de72346',
             0,
             'p2sh'),
    mtx.UTXO(2000000000,
             1,
             'a9140d0ac00bc19a7c697067b5f95741ed10ea345c8187',
             '64064449fc2aab13316e90beb6c2a224d86a08733ff5b48e422be7688de72346',
             0,
             'np2wsh'),
    # For MultiSigTestnet of WALLET_FORMAT_TEST_1/2
    mtx.UTXO(2000000000,
             1,
             'a914f132346e75e3a317f3090a07560fe75d74e1f51087',
             '64064449fc2aab13316e90beb6c2a224d86a08733ff5b48e422be7688de72346',
             0,
             'p2sh'),
    mtx.UTXO(2000000000,
             1,
             'a914d35515db546bb040e61651150343a218c87b471e87',
             '64064449fc2aab13316e90beb6c2a224d86a08733ff5b48e422be7688de72346',
             0,
             'np2wsh'),
    mtx.UTXO(2000000000,
             1,
             'a914af192b3600e705284f1e43c3cb9fdcf9e7ebe88187',
             '64064449fc2aab13316e90beb6c2a224d86a08733ff5b48e422be7688de72346',
             0,
             'p2sh'),
    mtx.UTXO(2000000000,
             1,
             'a914476b78c9d6e75adb92b0739e02eae5cbb043a68f87',
             '64064449fc2aab13316e90beb6c2a224d86a08733ff5b48e422be7688de72346',
             0,
             'p2sh'),
]


class Test_KeyManipultation(unittest.TestCase):

    def setUp(self):
        self._keybases = [util.CKey.make(b) for b in util.KeyBasis]

    def _every_keybase(self, assertion):
        [assertion(k) for k in self._keybases]

    def test_encode_decode(self):
        def check(key):
            self.assertEqual(key.base, len(key.source))

            def encdec(val):
                string = key.encode(val)
                val_ = key.decode(string)
                self.assertEqual(val, val_)
            # encdec(100)
            random.seed()
            for _ in range(10):
                encdec(random.randint(1, 1 << 256))
        self._every_keybase(check)

    def test_key_format(self):
        with self.assertRaises(key_format.KeyFormatError):
            key_format.KeyFormat.recognize("233")


class TestKey(unittest.TestCase):

    def test_wif(self):
        prv = key.PrivateKey.from_wif(WALLET_FORMAT_MAIN)
        self.assertEqual(WALLET_FORMAT_MAIN, prv.to_wif)

    def test_wif_compressed(self):
        # https://txid.io/wallet/#verify
        prv = key.PrivateKey.from_wif(WALLET_FORMAT_COMPRESSED_MAIN)
        self.assertEqual(prv.P2PKH, '1ExJJsNLQDNVVM1s1sdyt1o5P3GC5r32UG')
        self.assertEqual(prv.public_key.to_hex,
                         '033d5c2875c9bd116875a71a5db64cffcb13396b163d039b1d9327824891804334')
        self.assertEqual(
            prv.to_hex, 'c28a9f80738f770d527803a566cf6fc3edf6cea586c4fc4a5223a5ad797e1ac3')
        self.assertTrue(prv.compressed)
        self.assertEqual(WALLET_FORMAT_COMPRESSED_MAIN, prv.to_wif)

    def test_wif_test(self):
        prv = key.PrivateKey.from_wif(WALLET_FORMAT_TEST)
        self.assertEqual(WALLET_FORMAT_TEST, prv.to_wif)

    def test_wif_compressed_test(self):
        prv = key.PrivateKey.from_wif(WALLET_FORMAT_COMPRESSED_TEST)
        self.assertEqual(WALLET_FORMAT_COMPRESSED_TEST, prv.to_wif)


class Test_HD(unittest.TestCase):

    def _test_hierarchy_creation(self):
        gcd_ = gcd.GCD(None)
        km = gcd_.key_man
        km.generate_master_key()
        self.assertEqual(len(gcd_.all_enabled_coins) + 2, hd.Utils.keys_count)
        self.assertEqual(gcd_.btc_coin.private_key.chain_path, "/m/0'/0'")


class TestPrivateKey(unittest.TestCase):

    def test_address(self):
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_MAIN)
        self.assertEqual(private_key.P2PKH, BITCOIN_ADDRESS)
        self.assertIsNone(private_key.P2WPKH)
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_TEST)
        self.assertEqual(private_key.P2PKH, BITCOIN_ADDRESS_TEST)
        self.assertIsNone(private_key.P2WPKH)

    def test_scriptcode(self):
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_MAIN)
        self.assertEqual(
            b'\x00\x14\x92F\x1b\xdeb\x83\xb4a\xec\xe7\xdd\xf4\xdb\xf1\xe0\xa4\x8b\xd1\x13\xd8', private_key.segwit_scriptcode)
        self.assertEqual(
            b'v\xa9\x14\x92F\x1b\xdeb\x83\xb4a\xec\xe7\xdd\xf4\xdb\xf1\xe0\xa4\x8b\xd1\x13\xd8\x88\xac', private_key.scriptcode)

    def test_verify(self):
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_MAIN)
        data = os.urandom(200)
        signature = private_key.sign(data)
        self.assertTrue(private_key.verify(signature, data))
        self.assertFalse(private_key.verify(signature[:-1], data))
        self.assertFalse(private_key.verify(signature, data[2:]))
        #signature = private_key.sign(FINAL_TX_1.encode())
        #self.assertEqual( signature, b'0D\x02 ]BKc\x9fd\xe1\x99\t^\xab\xb1\x14\x93D\x88;\xdf\xd0wY\x07G\xcek\xe0\x98|\xaf\x11\n+\x02 `\x14?n/\xb2;\xd1\x0b\x84I*\xcd\xd0qvb~-\xa9\xa9\x02\xab\x18"\x8a\xb6\xc5\x80\xc11\r' )

    def test_segwit_address(self):
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_COMPRESSED_MAIN)
        self.assertEqual(private_key.P2WPKH, BITCOIN_ADDRESS_NP2WKH)
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_COMPRESSED_TEST)
        self.assertEqual(private_key.P2WPKH, BITCOIN_ADDRESS_TEST_NP2WKH)

    def test_to_wif(self):
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_MAIN)
        self.assertEqual(private_key.to_wif, WALLET_FORMAT_MAIN)
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_COMPRESSED_MAIN)
        self.assertEqual(private_key.to_wif, WALLET_FORMAT_COMPRESSED_MAIN)
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_TEST)
        self.assertEqual(private_key.to_wif, WALLET_FORMAT_TEST)
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_COMPRESSED_TEST)
        self.assertEqual(private_key.to_wif, WALLET_FORMAT_COMPRESSED_TEST)
        private_key = key.PrivateKey.from_wif(
            WALLET_LITECOIN_TEST, coin_network.LitecoinTestNetwork)

        self.assertEqual(private_key.network, coin_network.LitecoinTestNetwork)
        self.assertEqual(private_key.to_wif, WALLET_LITECOIN_TEST)


class TestBtcCore(unittest.TestCase):

    def test_valid(self):
        body = json.loads(TEST_DATA_PATH.joinpath(
            "key_io_valid.json").read_text())
        for idx, group in enumerate(body):
            props = group[2]
            if props['isPrivkey']:
                prv = key.PrivateKey.from_wif(group[0])
                self.assertEqual(prv.to_hex, group[1], idx)
                self.assertEqual(prv.compressed, props['isCompressed'], idx)
                # no equality - cause impossible distinguish regtest from test
                self.assertIn(prv.network.TITLE, props['chain'], (idx, group))

    def test_invalid(self):
        body = json.loads(TEST_DATA_PATH.joinpath(
            "key_io_invalid.json").read_text())
        for idx, group in enumerate(body):
            with self.assertRaises(key.KeyError, msg=idx):
                key.PrivateKey.from_wif(group[0])


class TestSignatureReal(unittest.TestCase):

    def test_sign(self):
        # from pybtc
        key_ = key.PrivateKey(
            bytes.fromhex('eb696a065ef48a2192da5b28b694f87544b30fae8327c4510137a922f32c6dcf'), None)

        self.assertEqual(key_.public_key.to_hex,
                         "03ad1d8e89212f0b92c74d23bb710c00662ad1470198ac48c43f7d6f93a2a26873")
        print("Sign message")
        msg = bytearray.fromhex(
            '64f3b0f4dd2bb3aa1ce8566d220cc74dda9df97d8490cc81d89d735c92e59fb6')
        sign = key_.sign(msg).hex()
        # self.assertEqual( sign,
        #                 "3044022047ac8e878352d3ebbde1c94ce3a10d057c24175747116f8288e5d794d12d482f0220217f36a485cae903c713331d877c1f64677e3622ad4010726870540656fe9dcb")
        print("Verify signature")
        from bmnclient.wallet import script
        s = '3044022047ac8e878352d3ebbde1c94ce3a10d057c24175747116f8288e5d794d12d482f0220217f36a485cae903c713331d877c1f64677e3622ad4010726870540656fe9dcb'
        self.assertTrue(script.verify_signature(
            s, key_.public_key.to_hex, msg))


class TestLitecoin(unittest.TestCase):
    WIF = '6ut8HoyTgiG12tfroAo6SQnquArWUi4z9wa7BPyRZnvFSANot6o'
    ADDR1 = 'LVqZnxtoDXGZ7qW9rHxkp1twhJC1TYgUkQ'
    ADDR2 = 'LWFvvfLCSpdSXzXgb6wUfwkfv6QDipAzJc'

    def test_main(self):
        key_ = key.PrivateKey.from_wif(
            self.WIF, coin_network.LitecoinMainNetwork)
        self.assertEqual(self.ADDR1, key_.P2PKH)
        self.assertEqual(self.WIF, key_.to_wif)

    def test_main2(self):
        key_ = key.PrivateKey(bytes.fromhex(
            'eb696a065ef48a2192da5b28b694f87544b30fae8327c4510137a922f32c6dcf'), coin_network.LitecoinMainNetwork)
        self.assertEqual(key_.public_key.to_hex.upper(
        ), '03AD1D8E89212F0B92C74D23BB710C00662AD1470198AC48C43F7D6F93A2A26873')
        self.assertEqual(
            key_.to_wif, 'TAwazXNuGfE4U3hVMLgAtgzw6tZu2sNF8igweoESTDBEfrnh1Jo4')
        self.assertEqual(key_.P2PKH, self.ADDR2)

    def test_scriptaddress(self):
        script1 = util.address_to_scriptpubkey(self.ADDR1)
        self.assertEqual(
            script1, b'v\xa9\x14tmy\xc1\xf7\xc4n\xd5[K#\\&\xb6O$+F\xb6\x1a\x88\xac')
        script2 = util.address_to_scriptpubkey(self.ADDR2)
        self.assertEqual(
            script2, b'v\xa9\x14y\t\x19r\x18lD\x9e\xb1\xde\xd2+x\xe4\r\x00\x9b\xdf\x00\x89\x88\xac')
        script3 = util.address_to_scriptpubkey(LITECOIN_ADDRESS).hex()
        self.assertEqual(
            script3, 'a914271c1bad2ebfec5ed79e999b99b092881284d79587')
        # real !!! https://blockchair.com/litecoin/transaction/d8a31d2768b295d4c5428d4bb168f76d68d44591d5be6cd19ea5995514a630be
        self.assertEqual(util.address_to_scriptpubkey('LQLno78Wtcme98eJ8YVii9u8eVvFbKeKUi').hex(
        ), '76a9143823a340794324b7ffee1d74a9ef663618b481ab88ac')

        # real !!! https://blockchair.com/litecoin/transaction/0f082a5eec8a3b33bac17c310de1885430f182510889f5172e110ff643a6ee4e
        self.assertEqual(util.address_to_scriptpubkey('MFQnMo3gaDcyoZ5trmcFUrjXMktM4NHzAd').hex(
        ), 'a914526319c4b9f519b194c175d508b48952467ac36087')
