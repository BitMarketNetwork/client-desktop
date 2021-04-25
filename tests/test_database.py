import logging
import os
import pathlib
import unittest

from bmnclient import gcd
import key_store
from bmnclient.wallet import address, coin_network, coins, hd, key
from bmnclient.database import db_wrapper, cipher

log = logging.getLogger(__name__)


class TestDataEncoding(unittest.TestCase):
    DB_NAME = "./test.db"
    PSW = b"some password"

    def test_crypt(self):
        self.__do_test(True)

    def test_plain(self):
        self.__do_test(False)

    def __do_test(self, encrypted: bool):
        cipher.Cipher.ENCRYPT = encrypted
        log.warning(f"start DB test crypted: {encrypted}")
        db = pathlib.Path(self.DB_NAME)
        if db.exists():
            db.unlink()
        db_wrapper.DbWrapper.DEBUG = True
        self.db = db_wrapper.DbWrapper(None)
        self.db.open_db(self.PSW, os.urandom(16) , self.DB_NAME)
        self.__test()
        self.db.drop_db()

    def __test(self):
        ENTRY = "some_key"
        ENRTY_VALUE = "some_value wth numbers 9090"
        self.assertIsNone(self.db._get_meta_entry(ENTRY))
        # import pdb; pdb.set_trace()
        self.db._set_meta_entry(ENTRY, ENRTY_VALUE)
        self.assertEqual(ENRTY_VALUE, self.db._get_meta_entry(ENTRY))
        ANOTHER_ENRTY_VALUE = "0xFFFFFFFFFFFFFFFFFF"
        self.db._set_meta_entry(ENTRY, ANOTHER_ENRTY_VALUE)
        self.assertEqual(ANOTHER_ENRTY_VALUE, self.db._get_meta_entry(ENTRY))
        ENTRY = "some_int"
        INTS = [0x2, 0xfffffffffff]
        self.assertIsNone(self.db._get_meta_entry(ENTRY))
        for int_ in INTS:
            self.db._set_meta_entry(ENTRY, int_)
            self.assertEqual(int_, int(self.db._get_meta_entry(ENTRY)))
        ENTRY = "some_real"
        REALS = [320329302.2809238409283, 0.1, 0.000002]
        for rl in REALS:
            self.db._set_meta_entry(ENTRY, rl)
            self.assertAlmostEqual(
                rl, float(self.db._get_meta_entry(ENTRY)), 5)
        ENTRY = "some_bool"
        self.db._set_meta_entry(ENTRY, True)
        self.assertTrue(self.db._get_meta_entry(ENTRY))
        self.db._set_meta_entry(ENTRY, False)
        self.assertFalse(int(self.db._get_meta_entry(ENTRY)))
        ENTRY = "null"
        self.assertIsNone(self.db._get_meta_entry(ENTRY))
        self.db._set_meta_entry(ENTRY, None)
        self.assertIsNone(self.db._get_meta_entry(ENTRY))
        HASH = os.urandom(32)
        self.db._set_meta_entry("seed", HASH)
        self.assertEqual(self.db._get_meta_entry("seed"),HASH)
        coin = coins.Bitcoin(None)
        coin.visible = False
        self.assertIsInstance(coin.visible, bool)
        self.db._add_coin(coin)
        self.assertFalse(coin.visible)
        coin.visible = True
        self.db._add_coin(coin)
        self.assertFalse(coin.visible)


class TestWorkflow(unittest.TestCase):

    def setUp(self):
        self.db = db_wrapper.DbWrapper(True)
        self.db.open_db( password=b'000' , nonce= os.urandom(16),db_name= "test.db")
        # beware.. it can make his own db !!!!
        self.gcd = gcd.GCD(False)

    def tearDown(self):
        ""
        # self.db.drop_db()

    @unittest.skip
    def test_addresses(self):
        coin = coins.BitcoinTest(self.gcd)
        seed = os.urandom(32)
        master_hd = hd.HDNode.make_master(
            seed, coin_network.BitcoinTestNetwork)
        coin.makeHdPath(master_hd)
        self.db._add_coin(coin, True)
        self.assertEqual(0, len(coin))
        addr = coin.make_address(key.AddressType.P2PKH)
        addr.balance = 3333
        addr.last_offset = 2344
        addr.first_offset = 8989
        self.assertEqual(1, len(coin))
        self.assertIsInstance(addr, address.CAddress)
        self.db._add_or_save_address(addr, None)
        coin._wallet_list.clear()
        self.assertEqual(0, len(coin))
        self.db._add_coin(coin, True)
        self.assertEqual(1, len(coin))
        _addr = coin.addressList[0]
        self.assertIsInstance(addr.first_offset, str)
        self.assertIsInstance(addr.last_offset, str)
        self.assertIsInstance(_addr.first_offset, str)
        self.assertIsInstance(_addr.last_offset, str)
        #!!
        self.assertEqual(addr, _addr)


class Test_password(unittest.TestCase):

    @unittest.skip
    def test_db(self):
        cipher.Cipher.ENCRYPT = True
        self.db = db_wrapper.DbWrapper(True)
        self.db.open_db("test.db")
        password = "test password stuff"
        self.db._set_meta_entry("password", password, strong=False)
        void = self.db._get_meta_entry("password")
        self.assertIsNone(void)
        self.assertTrue(self.db._test_hash(password))
        self.assertFalse(self.db._test_hash(password + "-"))

    @unittest.skip
    def test_higher_level(self):
        gcd_ = gcd.GCD(True, None)
        km = key_store.KeyStore(gcd_)
        gcd_.reset_db()
        self.assertFalse(gcd_.has_password())
        password = "test password stuff"
        km.setNewPassword(password)
        self.assertTrue(km.testPassword(password))
        self.assertFalse(km.testPassword(password*2))
        self.assertTrue(km.hasPassword)
        gcd_.reset_db()
        self.assertFalse(km.hasPassword)
