from __future__ import annotations

from os import urandom
from random import randint, shuffle
from typing import Sequence
from unittest import TestCase

from bmnclient.coins.abstract import Coin
from bmnclient.coins.coin_bitcoin import Bitcoin, BitcoinTest
from bmnclient.coins.coin_litecoin import Litecoin
from bmnclient.coins.hd import HdNode
from bmnclient.coins.list import CoinList
from bmnclient.language import Locale
from bmnclient.utils import DeserializeFlag, SerializeFlag
from tests.helpers import TestCaseApplication

BITCOIN_ADDRESS_LIST = (
    (
        "1PMycacnJaSqwwJqjawXBErnLsZ7RkXUAs", # noqa
        Bitcoin.Address.Type.PUBKEY_HASH,
        0,
        "f54a5851e9372b87810a8e60cdd2e7cfd80b6e31"
    ), (
        "3Ps86GT6vHg7dCT5QhcECDFkRaUJbBzqXB",
        Bitcoin.Address.Type.SCRIPT_HASH,
        5,
        "f33c134a48d70818bdc2cf09631316ce90f71366"
    ), (
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", # noqa
        Bitcoin.Address.Type.WITNESS_V0_KEY_HASH,
        0,
        "751e76e8199196d454941c45d1b3a323f1433bd6"
    ), (
        "bc1qeklep85ntjz4605drds6aww9u0qr46qzrv5xswd35uhjuj8ahfcqgf6hak", # noqa
        Bitcoin.Address.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "cdbf909e935c855d3e8d1b61aeb9c5e3c03ae8021b286839b1a72f2e48fdba70" # noqa
    ), (
        "bc1sw50qa3jx3s",
        Bitcoin.Address.Type.WITNESS_UNKNOWN,
        16,
        "751e"
    ), (
        "bc1gmk9yu",
        None,
        None,
        None
    ), (
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P", # noqa
        None,
        None,
        None
    )
)

BITCOIN_TEST_ADDRESS_LIST = (
    (
        "mxVFsFW5N4mu1HPkxPttorvocvzeZ7KZyk", # noqa
        BitcoinTest.Address.Type.PUBKEY_HASH,
        0x6f,
        "ba27f99e007c7f605a8305e318c1abde3cd220ac" # noqa
    ), (
       "n49mqVncWxMYwCmZDHXba3Y9RVPzAFTUoX",
       BitcoinTest.Address.Type.PUBKEY_HASH,
       0x6f,
       "f8496d9390c68a99b96e7c438af90f316739a839"
    ), (
        "2N7EFdToQVZviaVC2Wfkidm6HzntiqtVmDE", # noqa
        BitcoinTest.Address.Type.SCRIPT_HASH,
        0xc4,
        "9962b7013858273326d2e36057bde8c844f831a1"
    ), (
        "tb1qu03l73f3rdcjh0ywnhc8vc3yp5gumvgummhv7f", # noqa
        BitcoinTest.Address.Type.WITNESS_V0_KEY_HASH,
        0,
        "e3e3ff45311b712bbc8e9df07662240d11cdb11c"
    ), (
        "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy", # noqa
        BitcoinTest.Address.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433"
    ), (
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7", # noqa
        BitcoinTest.Address.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "1863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262"
    ), (
        "tb1s424qnvez45", # noqa
        BitcoinTest.Address.Type.WITNESS_UNKNOWN,
        16,
        "aaaa" # noqa
    ),
)

LITECOIN_ADDRESS_LIST = (
    (
        "LaMT348PWRnrqeeWArpwQPbuanpXDZGEUz", # noqa
        Litecoin.Address.Type.PUBKEY_HASH,
        0x30,
        "a5f4d12ce3685781b227c1f39548ddef429e9783" # noqa
    ), (
        "MQMcJhpWHYVeQArcZR3sBgyPZxxRtnH441",
        Litecoin.Address.Type.SCRIPT_HASH,
        0x32,
        "b48297bff5dadecc5f36145cec6a5f20d57c8f9b" # noqa
    ), (
        "ltc1q7nlrhuxks5rvc7aumcpzttm3xll3f5zqlp0pyv", # noqa
        Litecoin.Address.Type.WITNESS_V0_KEY_HASH,
        0,
        "f4fe3bf0d68506cc7bbcde0225af7137ff14d040" # noqa
    ), (
        "ltc1q5det08ke2gpet06wczcdfs2v3hgfqllxw28uln8vxxx82qlue6uswceljm", # noqa
        Litecoin.Address.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "a372b79ed9520395bf4ec0b0d4c14c8dd0907fe6728fcfccec318c7503fcceb9" # noqa
    )
)


def fillCoin(
        owner: TestCase,
        coin: Coin,
        *,
        address_count: int = 4,
        tx_count: int = 4) -> Coin:
    root_node = HdNode.deriveRootNode(urandom(64))
    owner.assertIsNotNone(root_node)

    owner.assertTrue(coin.deriveHdNode(root_node))
    coin.height = randint(1000, 100000)
    coin.offset = "offset" + str(randint(1000, 100000))
    coin.unverifiedOffset = "u_offset" + str(randint(1000, 100000))
    coin.unverifiedHash = "u_hash" + str(randint(1000, 100000))
    coin.verifiedHeight = randint(1000, 100000)
    owner.assertTrue(coin.save())

    for address_index in range(1, address_count + 1):
        address = coin.deriveHdAddress(
            account=0,
            is_change=False,
            balance=randint(1000, 100000),
            tx_count=randint(1000, 100000),
            label="address label " + str(address_index),
            comment="address comment " + str(address_index),
            history_first_offset="first_" + str(randint(1000, 100000)),
            history_last_offset="last_" + str(randint(1000, 100000)))
        owner.assertIsNotNone(address)
        owner.assertTrue(address.save())

        for tx_index in range(1, tx_count + 1):
            tx = coin.Tx(
                coin,
                name="tx_name_" + str(tx_index) + "_" + address.name,
                height=randint(10000, 1000000),
                time=randint(10000, 1000000),
                amount=randint(10000, 1000000),
                fee_amount=randint(10000, 1000000),
                is_coinbase=randint(0, 2) == 1,
                input_list=[],
                output_list=[])
            owner.assertTrue(tx.save())
            owner.assertTrue(address.associate(tx))

            for i in range(1, 3):
                input_address = coin.deriveHdAddress(
                    account=1,
                    is_change=False)
                owner.assertIsNotNone(input_address)
                io = coin.Tx.Io(
                    tx,
                    io_type=coin.Tx.Io.IoType.INPUT,
                    index=i,
                    output_type="output_type_" + str(i),
                    address=input_address,
                    amount=randint(1000, 100000))
                owner.assertFalse(io.address.isNullData)
                owner.assertTrue(io.save())

            for i in range(1, 3):
                output_address = coin.deriveHdAddress(
                    account=2,
                    is_change=False)
                owner.assertIsNotNone(output_address)
                io = coin.Tx.Io(
                    tx,
                    io_type=coin.Tx.Io.IoType.OUTPUT,
                    index=i,
                    output_type="output_type_" + str(i),
                    address=output_address,
                    amount=randint(1000, 100000))
                owner.assertFalse(io.address.isNullData)
                owner.assertTrue(io.save())
            io = coin.Tx.Io(
                tx,
                io_type=coin.Tx.Io.IoType.OUTPUT,
                index=4,
                output_type="output_type_nulldata",
                address=coin.Address.createNullData(coin),
                amount=0)
            owner.assertTrue(io.address.isNullData)
            owner.assertTrue(io.save())

        for i in range(1, 3):
            utxo = coin.Tx.Utxo(
                address,
                script_type=address.type.value.scriptType,
                name="utxo_" + str(i),
                height=randint(10000, 1000000),
                index=randint(10000, 1000000),
                amount=randint(10000, 1000000))
            owner.assertTrue(utxo.save())

        owner.assertEqual(tx_count, len(address.txList))
    return coin


class TestCoins(TestCaseApplication):
    def _test_address_decode(
            self,
            coin: Coin,
            address_list: tuple[tuple, ...]) -> None:
        hash_check_count = 0

        # noinspection PyUnusedLocal
        for (name, type_, version, hash_) in address_list:
            address = coin.Address.createFromName(coin, name=name)
            if type_ is None:
                self.assertIsNone(address)
            else:
                self.assertIsNotNone(address)
                self.assertEqual(type_, address.type)
                if hash_:
                    self.assertEqual(hash_, address.hash.hex())
                    hash_check_count += 1
                else:
                    self.assertEqual(b"", address.hash)
        self.assertTrue(hash_check_count > 0)

    def test_address_decode(self) -> None:
        self._test_address_decode(
            Bitcoin(model_factory=self._application.modelFactory),
            BITCOIN_ADDRESS_LIST)
        self._test_address_decode(
            BitcoinTest(model_factory=self._application.modelFactory),
            BITCOIN_TEST_ADDRESS_LIST)
        self._test_address_decode(
            Litecoin(model_factory=self._application.modelFactory),
            LITECOIN_ADDRESS_LIST)

    def test_string_to_amount(self) -> None:
        b = Bitcoin.Currency
        satoshi_value = 10 ** 8

        for v in ("", "-", "+", "-.", "+.", "."):
            self.assertIsNone(b.fromString(v))

        for v in ("--11", "++11", "-+11", "+-11", " 11", "11 ", "11. "):
            self.assertIsNone(b.fromString(v))

        for (r, v) in (
                (0, "0"),
                (50 * satoshi_value, "50"),
                (-50 * satoshi_value, "-50"),
                (60 * satoshi_value, "60."),
                (-60 * satoshi_value, "-60."),

                (None, "60.123456789"),
                (None, "-60.123456789"),

                (6012345678, "60.12345678"),
                (-6012345678, "-60.12345678"),
                (6010000000, "60.1"),
                (-6010000000, "-60.1"),
                (6010000000, "60.10"),
                (-6010000000, "-60.10"),
                (6012345670, "60.1234567"),
                (-6012345670, "-60.1234567"),
                (12345670, "0.1234567"),
                (-12345670, "-0.1234567"),
                (11234567, ".11234567"),
                (-11234567, "-.11234567"),
                (11234567, "+.11234567"),

                (0, "-0.00000000"),
                (0, "+0.00000000"),

                (-99999999, "-0.99999999"),
                (None, "-0.099999999"),

                (99999999, "0.99999999"),
                (None, "-0.099999999"),

                (-92233720368 * satoshi_value, "-92233720368"),
                (None, "-92233720369"),

                (92233720368 * satoshi_value, "92233720368"),
                (None, "92233720369"),

                (92233720368 * satoshi_value, "+92233720368"),
                (None, "+92233720369"),

                (-(2 ** 63), "-92233720368.54775808"),
                (None, "92233720369"),

                ((2 ** 63) - 1, "92233720368.54775807"),
                (None, "92233720368.54775808"),

                ((2 ** 63) - 1, "+92233720368.54775807"),
        ):
            self.assertEqual(r, b.fromString(v))

    def test_string_to_amount_locale(self) -> None:
        b = BitcoinTest.Currency
        locale = Locale("en_US")
        for (r, v) in (
                (0, "0"),
                (500000012345678, "5000000.12345678"),
                (500000122345678, "5,000,001.22345678"),
                (500000222345678, "+5,000,002.22345678"),
                (-500000322345678, "-5,000,003.22345678"),
                (None, " 5,000,000.32345678"),
                (None, "5,000,000 .42345678"),
                (None, "5.000,000.52345678"),
                (None, "5 000 000.62345678"),
                (99999999, "0.99999999"),
                (-99999999, "-0.99999999"),
        ):
            self.assertEqual(r, b.fromString(v, locale=locale))

    def test_amount_to_string(self) -> None:
        b = Bitcoin.Currency

        self.assertEqual("0", b.toString(0))
        self.assertEqual("-1", b.toString(-1 * 10 ** 8))
        self.assertEqual("1", b.toString(+1 * 10 ** 8))

        for (s, d) in (
                (1, "0.00000001"),
                (10, "0.0000001"),
                (1000, "0.00001"),
                (1200000, "0.012"),
                (880000000, "8.8"),
                (880000001, "8.80000001"),
                (880000010, "8.8000001"),
                (88000000000, "880")
        ):
            self.assertEqual("-" + d, b.toString(-s))
            self.assertEqual(d, b.toString(s))

        self.assertEqual(
            "92233720368.54775807",
            b.toString(9223372036854775807))
        self.assertEqual(
            "0",
            b.toString(9223372036854775808))
        self.assertEqual(
            "-92233720368.54775808",
            b.toString(-9223372036854775808))
        self.assertEqual(
            "0",
            b.toString(-9223372036854775809))

    def test_mempool_address_lists(self) -> None:
        for limit in range(201):
            coin = Bitcoin(model_factory=self._application.modelFactory)
            root_node = HdNode.deriveRootNode(urandom(64))
            self.assertIsNotNone(root_node)
            self.assertTrue(coin.deriveHdNode(root_node))
            self.assertTrue(coin.save())

            for i in range(limit):
                address = coin.deriveHdAddress(
                    account=0,
                    index=1000 + i,
                    is_change=False)
                self.assertIsNotNone(address)
                self.assertTrue(address.save())
            self.assertEqual(limit, len(coin.addressList))

            limit = randint(1, 10)

            # create
            mempool_list = coin.createMempoolAddressLists(limit)
            count = 0
            for v in mempool_list:
                count += len(v["list"])
                self.assertIsInstance(v["local_hash"], bytes)
                self.assertIsNone(v["remote_hash"])
                self.assertLessEqual(len(v["list"]), limit)
            self.assertEqual(count, len(coin.addressList))

            # noinspection PyProtectedMember
            self.assertEqual(len(coin._mempool_cache), len(mempool_list))

            # set result
            for (i, v) in enumerate(mempool_list):
                self.assertTrue(coin.setMempoolAddressListResult(
                    v["local_hash"],
                    "hash_{:06d}".format(i)))

            # create again
            mempool_list = coin.createMempoolAddressLists(limit)
            for (i, v) in enumerate(mempool_list):
                self.assertIsInstance(v["local_hash"], bytes)
                self.assertIsInstance(v["remote_hash"], str)
                self.assertEqual(v["remote_hash"], "hash_{:06d}".format(i))
                self.assertLessEqual(len(v["list"]), limit)

            # noinspection PyProtectedMember
            self.assertEqual(len(coin._mempool_cache), len(mempool_list))

            # check expired
            for i in range(randint(1, 20)):
                address = coin.deriveHdAddress(
                    account=0,
                    index=10000 + i,
                    is_change=False)
                self.assertIsNotNone(address)
                self.assertTrue(address.save())

                mempool_list = coin.createMempoolAddressLists(limit)
                # noinspection PyProtectedMember
                self.assertEqual(len(coin._mempool_cache), len(mempool_list))

    def test_utxo_1(self) -> None:
        coin = Bitcoin(model_factory=self._application.modelFactory)
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertTrue(coin.deriveHdNode(root_node))
        self.assertTrue(coin.save())

        address1 = coin.deriveHdAddress(account=0, index=1, is_change=False)
        address2 = coin.deriveHdAddress(account=0, index=2, is_change=False)
        self.assertNotEqual(address1, address2)

        for address in (address1, address2):
            for i in range(100):
                utxo = coin.Tx.Utxo(
                    address,
                    script_type=address.type.value.scriptType,
                    name="utxo_" + str(i),
                    index=i,
                    height=i * 1000,
                    amount=i * 10000)
                self.assertFalse(utxo.save())
            self.assertTrue(address.save())

        for address in (address1, address2):
            for i in range(100):
                utxo = coin.Tx.Utxo(
                    address,
                    script_type=address.type.value.scriptType,
                    name="utxo_" + str(i),
                    index=i,
                    height=i * 1000,
                    amount=i * 10000)
                self.assertTrue(utxo.save())
                self.assertLess(-1, utxo.rowId)

        for address in (address1, address2):
            self.assertRaises(
                KeyError,
                coin.Tx.Utxo,
                address,
                name="utxo_X")

        for i in range(100):
            utxo = coin.Tx.Utxo(address1, name="utxo_" + str(i))
            self.assertEqual(address1.type.value.scriptType, utxo.scriptType)
            self.assertEqual("utxo_" + str(i), utxo.name)
            self.assertEqual(i, utxo.index)
            self.assertEqual(i * 1000, utxo.height)
            self.assertEqual(i * 10000, utxo.amount)
            self.assertLess(0, utxo.rowId)

        self.assertEqual(100, len(address1.utxoList))
        self.assertEqual(100, len(address2.utxoList))

        for i in range(100):
            utxo = coin.Tx.Utxo(address1, name="utxo_" + str(i))
            self.assertTrue(utxo.remove())
            self.assertEqual(-1, utxo.rowId)
            self.assertFalse(utxo.remove())

        self.assertEqual(0, len(address1.utxoList))
        self.assertEqual(100, len(address2.utxoList))
        for utxo in address2.utxoList:
            self.assertLess(0, utxo.rowId)
            self.assertIs(address2, utxo.address)

    def test_io(self) -> None:
        coin = Bitcoin(model_factory=self._application.modelFactory)
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertTrue(coin.deriveHdNode(root_node))
        self.assertTrue(coin.save())

        for tx_index in range(10):
            tx = coin.Tx(
                coin,
                name="tx_name_" + str(tx_index),
                height=randint(10000, 1000000),
                time=randint(10000, 1000000),
                amount=randint(10000, 1000000),
                fee_amount=randint(10000, 1000000),
                is_coinbase=randint(0, 2) == 1,
                input_list=[],
                output_list=[])
            self.assertTrue(tx.save())
            self.assertEqual(0, len(tx.inputList))
            self.assertEqual(0, len(tx.outputList))

            for io_type in tx.Io.IoType:
                for io_index in range(10):
                    if not io_index:
                        io_address = coin.deriveHdAddress(
                            account=hash(io_type),
                            index=io_index,
                            is_change=False)
                        self.assertFalse(io_address.isNullData)
                    else:
                        io_address = coin.Address.createNullData(
                            coin,
                            name=f"address_{io_type.value}_{io_index}")
                        self.assertTrue(io_address.isNullData)
                    self.assertIsNotNone(io_address)

                    io = tx.Io(
                        tx,
                        io_type=io_type,
                        index=io_index,
                        output_type=f"output_type_{io_type.value}_{io_index}",
                        address=io_address,
                        amount=io_index * 100000)
                    self.assertTrue(io.address)
                    self.assertEqual(
                        io_address.isNullData,
                        io.address.isNullData)
                    self.assertTrue(io.save())
                    self.assertLess(-1, io.rowId)

                    io_db = tx.Io(tx, io_type=io_type, index=io_index)
                    self.assertEqual(io.IoType, io_db.IoType)
                    self.assertEqual(io.index, io_db.index)
                    self.assertEqual(io.outputType, io_db.outputType)
                    self.assertEqual(io.address, io_db.address)
                    self.assertTrue(io_db.address)
                    self.assertEqual(
                        io_address.isNullData,
                        io_db.address.isNullData)
                    self.assertLess(0, io_db.rowId)

                    self.assertRaises(
                        AssertionError,
                        tx.Io,
                        tx,
                        io_type=None,
                        index=0)

            self.assertEqual(10, len(tx.inputList))
            self.assertEqual(10, len(tx.outputList))

    def _test_serialization(
            self,
            d_flags: DeserializeFlag,
            coin_type: type(Coin)) -> None:
        coin = fillCoin(
            self,
            coin_type(model_factory=self._application.modelFactory))

        data = coin.serialize(SerializeFlag.PRIVATE_MODE)
        self.assertIsInstance(data, dict)

        # from pprint import pprint
        # pprint(data, sort_dicts=False)

        coin_new = coin_type(model_factory=self._application.modelFactory)
        coin_new.deserializeUpdate(d_flags, data)
        self.assertTrue(coin_new.save())

        # coin compare
        self.assertEqual(coin.name, coin_new.name)
        self.assertEqual(coin.height, coin_new.height)
        self.assertEqual(coin.offset, coin_new.offset)
        self.assertEqual(coin.unverifiedOffset, coin_new.unverifiedOffset)
        self.assertEqual(coin.unverifiedHash, coin_new.unverifiedHash)
        self.assertEqual(coin.verifiedHeight, coin_new.verifiedHeight)

        # address list compare
        self.assertEqual(len(coin.addressList), len(coin_new.addressList))
        for address_index in range(len(coin.addressList)):
            a1 = coin.addressList[address_index]
            a2 = coin_new.addressList[address_index]
            self.assertIsNot(a1, a2)
            self.assertEqual(a1.name, a2.name)
            self.assertEqual(a1.exportKey(), a2.exportKey())
            self.assertEqual(a1.balance, a2.balance)
            self.assertEqual(a1.txCount, a2.txCount)
            self.assertEqual(a1.label, a2.label)
            self.assertEqual(a1.comment, a2.comment)
            self.assertEqual(a1.historyFirstOffset, a2.historyFirstOffset)
            self.assertEqual(a1.historyLastOffset, a2.historyLastOffset)

            # tx list compare
            self.assertEqual(len(a1.txList), len(a2.txList))
            for tx_index in range(len(a1.txList)):
                t1 = a1.txList[tx_index]
                t2 = a2.txList[tx_index]
                self.assertEqual(t1.name, t2.name)
                self.assertEqual(t1.height, t2.height)
                self.assertEqual(t1.time, t2.time)
                self.assertEqual(t1.amount, t2.amount)
                self.assertEqual(t1.feeAmount, t2.feeAmount)
                self.assertEqual(t1.isCoinbase, t2.isCoinbase)

                # io list compare
                self.assertEqual(len(t1.inputList), len(t2.inputList))
                self.assertEqual(len(t1.outputList), len(t2.outputList))
                for io_index in range(len(t1.inputList)):
                    io1 = t1.inputList[io_index]
                    io2 = t2.inputList[io_index]
                    self.assertEqual(io1.outputType, io2.outputType)
                    self.assertEqual(io1.address.name, io2.address.name)
                    self.assertEqual(io1.address.balance, io2.address.balance)
                for io_index in range(len(t1.outputList)):
                    io1 = t1.outputList[io_index]
                    io2 = t2.outputList[io_index]
                    self.assertEqual(io1.outputType, io2.outputType)
                    self.assertEqual(io1.address.name, io2.address.name)
                    self.assertEqual(io1.address.balance, io2.address.balance)

            # utxo list compare
            self.assertEqual(len(a1.utxoList), len(a2.utxoList))
            for utxo_index in range(len(a1.utxoList)):
                u1 = a1.utxoList[utxo_index]
                u2 = a2.utxoList[utxo_index]
                self.assertEqual(u1.name, u2.name)
                self.assertEqual(u1.height, u2.height)
                self.assertEqual(u1.index, u2.index)
                self.assertEqual(u1.amount, u2.amount)

    def test_serialization(self) -> None:
        for coin in CoinList(model_factory=self._application.modelFactory):
            self.assertTrue(coin.save())
            for d_flag in DeserializeFlag:
                self._test_serialization(d_flag, coin.__class__)


class TestTxFactory(TestCaseApplication):
    def setUp(self) -> None:
        super().setUp()
        self._coin = Bitcoin(model_factory=self._application.modelFactory)
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)
        self.assertTrue(self._coin.deriveHdNode(root_node))
        self.assertTrue(self._coin.save())

    def _createUtxoList(
            self,
            address: Bitcoin.Address,
            amount_list: Sequence[int]) -> None:
        for i in range(len(amount_list)):
            utxo = self._coin.Tx.Utxo(
                address,
                script_type=address.type.value.scriptType,
                name=i.to_bytes(32, "big").hex(),
                height=100 + i,
                index=0,
                amount=amount_list[i])
            self.assertTrue(utxo.save())

    @classmethod
    def _isLowHeightUtxo(
            cls,
            utxo_list: Sequence[Bitcoin.Tx.Utxo],
            utxo):
        result = False
        for far_utxo in utxo_list:
            if far_utxo.amount == utxo.amount:
                if far_utxo is not utxo and far_utxo.height > utxo.height:
                    result = True
        return result

    def test_find_exact_utxo(self) -> None:
        address = self._coin.deriveHdAddress(account=0, is_change=False)
        self.assertIsNotNone(address)
        self.assertTrue(address.save())

        # no utxo
        for r in range(100):
            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, r)
            self.assertIsNone(utxo)

        # single utxo with amount 0, 1
        if True:
            for amount in (0, 1):
                self._createUtxoList(address, (amount, ))
                # noinspection PyProtectedMember
                utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 0)
                if not amount:
                    self.assertIsNotNone(utxo)
                    self.assertEqual(amount, utxo.amount)
                else:
                    self.assertIsNone(utxo)

                # noinspection PyProtectedMember
                utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 1)
                if not amount:
                    self.assertIsNone(utxo)
                else:
                    self.assertIsNotNone(utxo)
                    self.assertEqual(amount, utxo.amount)

                # noinspection PyProtectedMember
                utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 2)
                self.assertIsNone(utxo)
                for utxo in address.utxoList:
                    self.assertTrue(utxo.remove())
                    self.assertEqual(-1, utxo.rowId)

        # multiple utxo
        if True:
            self._createUtxoList(address, (0, 1, 2, 3, 4, 5, 6, 6))

            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 7)
            self.assertIsNone(utxo)

            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 6)
            self.assertIsNotNone(utxo)
            self.assertEqual(6, utxo.amount)
            self.assertTrue(self._isLowHeightUtxo(address.utxoList, utxo))

            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 4)
            self.assertIsNotNone(utxo)
            self.assertEqual(4, utxo.amount)

    def test_find_single_address_single_utxo(self) -> None:
        address = self._coin.deriveHdAddress(account=0, is_change=False)
        self.assertIsNotNone(address)
        self.assertTrue(address.save())

        # find same amount
        if True:
            amount_list = [x for x in range(1000)]
            shuffle(amount_list)
            self._createUtxoList(address, amount_list)
            self.assertEqual(1000, len(address.utxoList))
            for i in range(len(address.utxoList)):
                # noinspection PyProtectedMember
                l, a = self._coin.TxFactory._findOptimalUtxoList(
                    address.utxoList,
                    i)
                self.assertEqual(1, len(l))
                self.assertEqual(i, a)

        for utxo in address.utxoList:
            self.assertTrue(utxo.remove())
            self.assertEqual(-1, utxo.rowId)

        # find the nearest amount + height test
        if True:
            amount_list = list(range(1, 1000, 2)) + list(range(1, 1000, 2))
            shuffle(amount_list)
            self._createUtxoList(address, amount_list)
            self.assertEqual(500 * 2, len(address.utxoList))
            for i in range(0, 1000, 2):
                # noinspection PyProtectedMember
                l, a = self._coin.TxFactory._findOptimalUtxoList(
                    address.utxoList,
                    i)
                self.assertEqual(1, len(l))
                self.assertEqual(i + 1, a)
                self.assertTrue(self._isLowHeightUtxo(address.utxoList, l[0]))

    def test_find_single_address_multiple_utxo(self) -> None:
        address = self._coin.deriveHdAddress(account=0, is_change=False)
        self.assertIsNotNone(address)
        self.assertTrue(address.save())

        amount_list = list(range(0, 10)) * 4
        shuffle(amount_list)
        self._createUtxoList(address, amount_list)
        self.assertEqual(40, len(address.utxoList))

        test_list = (
            (9, 9, 1),
            (10, 10, 2),
            (21, 21, 3),
            (28, 28, 4),
            (29, 29, 4),
            (100, 102, 13),
            (200, 0, 0),
        )

        for (amount, result_amount, utxo_count) in test_list:
            # noinspection PyProtectedMember
            l, a = self._coin.TxFactory._findOptimalUtxoList(
                address.utxoList,
                amount)
            self.assertEqual(utxo_count, len(l))
            self.assertEqual(result_amount, a)

        for utxo in address.utxoList:
            self.assertTrue(utxo.remove())
            self.assertEqual(-1, utxo.rowId)

        amount_list = list(range(1, 10))
        shuffle(amount_list)
        self._createUtxoList(address, amount_list)
        self.assertEqual(9, len(address.utxoList))

        test_list = (
            (9, 9, 1),
            (10, 11, 2),
            (20, 21, 3),
            (45, 45, 9),
        )

        for (amount, result_amount, utxo_count) in test_list:
            # noinspection PyProtectedMember
            l, a = self._coin.TxFactory._findOptimalUtxoList(
                address.utxoList,
                amount)
            self.assertEqual(utxo_count, len(l))
            self.assertEqual(result_amount, a)

    def test(self) -> None:
        amount_list = list(range(100000, 100100))
        address = self._coin.deriveHdAddress(
            account=0,
            is_change=False,
            index=1000)
        self.assertIsNotNone(address)
        self.assertTrue(address.save())

        receiver_address = self._coin.deriveHdAddress(
            account=0,
            is_change=False,
            index=1001)
        self.assertIsNotNone(receiver_address)

        self._createUtxoList(address, amount_list)
        self.assertTrue(address.save())
        self.assertEqual(1, len(self._coin.addressList))

        txf = self._coin.txFactory
        txf.updateUtxoList()
        self.assertIsNone(txf.name)
        self.assertIsNone(txf.receiverAddress)
        self.assertIsNone(txf.changeAddress)
        self.assertFalse(txf.subtractFee)
        self.assertEqual(sum(amount_list), txf.availableAmount)
        self.assertEqual(0, txf.receiverAmount)

        txf.inputAddressList.clear()
        self.assertEqual(0, len(txf.inputAddressList))
        self.assertFalse(txf.inputAddressList.append("BAD_INPUT1"))
        self.assertEqual(0, len(txf.inputAddressList))
        self.assertTrue(txf.inputAddressList.append(
            "3Ps86GT6vHg7dCT5QhcECDFkRaUJbBzqXB"))
        self.assertEqual(1, len(txf.inputAddressList))
        self.assertFalse(txf.inputAddressList.append("BAD_INPUT2"))
        self.assertEqual(1, len(txf.inputAddressList))
        txf.inputAddressList.clear()
        self.assertEqual(0, len(txf.inputAddressList))

        self.assertEqual(0, txf.setReceiverMaxAmount())
        self.assertFalse(txf.isValidReceiverAmount)
        self.assertFalse(txf.isValidFeeAmount)
        self.assertFalse(txf.setReceiverAddressName("BAD_NAME"))
        self.assertTrue(txf.setReceiverAddressName(receiver_address.name))
        self.assertEqual(txf.receiverAddress, receiver_address)

        address_count = len(self._coin.addressList)
        self.assertEqual(1, address_count)

        for subtract_fee in (False, True):
            txf.subtractFee = subtract_fee
            self.assertEqual(subtract_fee, txf.subtractFee)

            if True:
                receiver_amount = txf.setReceiverMaxAmount()
                self.assertEqual(receiver_amount, txf.receiverAmount)
                self.assertTrue(txf.isValidReceiverAmount)
                self.assertTrue(txf.isValidFeeAmount)
                self.assertEqual(0, txf.changeAmount)

                if subtract_fee:
                    self.assertEqual(sum(amount_list), receiver_amount)
                    self.assertEqual(receiver_amount, txf.availableAmount)
                else:
                    self.assertLess(1, receiver_amount)
                    self.assertGreater(sum(amount_list), receiver_amount)
                    self.assertLess(receiver_amount, txf.availableAmount)
                    self.assertEqual(
                        txf.availableAmount - receiver_amount,
                        txf.feeAmount)

                self.assertTrue(txf.prepare())
                self.assertIsNone(txf.name)
                self.assertIsNone(txf.changeAddress)
                self.assertTrue(txf.sign())
                self.assertIsNotNone(txf.name)
                self.assertTrue(txf.broadcast())
                self.assertIsNone(txf.name)
                self.assertEqual(address_count, len(self._coin.addressList))
                txf.clear()

            if True:
                receiver_amount = sum(amount_list)
                if subtract_fee:
                    receiver_amount += 1
                txf.receiverAmount = receiver_amount
                self.assertEqual(receiver_amount, txf.receiverAmount)
                self.assertFalse(txf.isValidReceiverAmount)
                self.assertFalse(txf.isValidFeeAmount)
                self.assertIsNone(txf.changeAmount)
                self.assertFalse(txf.prepare())
                self.assertIsNone(txf.name)
                self.assertIsNone(txf.changeAddress)
                self.assertFalse(txf.sign())
                self.assertIsNone(txf.name)
                self.assertFalse(txf.broadcast())
                txf.clear()

            if True:
                receiver_amount = randint(
                    sum(amount_list) // 9,
                    sum(amount_list) // 3)

                txf.receiverAmount = receiver_amount
                self.assertEqual(receiver_amount, txf.receiverAmount)
                self.assertTrue(txf.isValidReceiverAmount)
                self.assertTrue(txf.isValidFeeAmount)
                self.assertLess(1, txf.feeAmount)
                self.assertLessEqual(0, txf.changeAmount)

                self.assertTrue(txf.prepare())
                self.assertIsNone(txf.name)
                if txf.changeAmount > 0:
                    self.assertIsNotNone(txf.changeAddress)
                else:
                    self.assertIsNone(txf.changeAddress)
                self.assertTrue(txf.sign())
                self.assertIsNotNone(txf.name)

                # noinspection PyProtectedMember
                self.assertEqual(txf.feeAmount, txf._mtx.feeAmount)
                if subtract_fee:
                    # noinspection PyProtectedMember
                    self.assertEqual(
                        txf.receiverAmount + txf.changeAmount,
                        txf._mtx.amount)
                else:
                    # noinspection PyProtectedMember
                    self.assertEqual(
                        txf.receiverAmount + txf.changeAmount + txf.feeAmount,
                        txf._mtx.amount)

                self.assertTrue(txf.broadcast())
                self.assertIsNone(txf.name)
                if txf.changeAmount > 0:
                    address_count += 1
                    self.assertEqual(address_count, len(self._coin.addressList))
                txf.clear()


class TestMutableTx(TestCaseApplication):
    def setUp(self) -> None:
        super().setUp()
        self._coin = Bitcoin(model_factory=self._application.modelFactory)
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)
        self.assertTrue(self._coin.deriveHdNode(root_node))

    def _createInput(
            self,
            coin: Coin,
            name: str,
            index: int,
            *,
            private_key: str,
            address_type: Coin.Address.Type,
            script_type: Coin.Address.Script.Type,
            amount: int,
            sequence: int,
            is_dummy: bool = False) -> dict:
        private_key = coin.Address.importKey(coin, private_key)
        self.assertIsNotNone(private_key)

        address = coin.Address.create(
            self._coin,
            type_=address_type,
            key=private_key)
        self.assertIsNotNone(address)

        utxo = coin.Tx.Utxo(
            address,
            name=bytes.fromhex(name)[::-1].hex(),
            index=index,
            height=1,
            amount=amount,
            script_type=script_type)

        return dict(
            utxo=utxo,
            sequence=sequence,
            is_dummy=is_dummy)

    @classmethod
    def _createOutput(
            cls,
            coin: Coin,
            *,
            address_name: str,
            amount: int,
            is_dummy: bool = False) -> dict:
        address = coin.Address.createFromName(coin, name=address_name)
        return dict(
            address=address,
            amount=amount,
            is_dummy=is_dummy)

    def _test_mtx(
            self,
            input_list: list[dict],
            output_list: list[dict],
            *,
            lock_time: int,
            is_dummy: bool,
            expected_name: str | None,
            expected_data: str,
            excepted_raw_size: int,
            excepted_virtual_size: int) -> Coin.TxFactory.MutableTx:
        mtx = self._coin.TxFactory.MutableTx(
            self._coin,
            lock_time=lock_time,
            is_dummy=is_dummy)
        self.assertEqual(0, mtx.amount)
        self.assertEqual(0, mtx.feeAmount)

        for io in input_list:
            mtx.inputList.append(io)
        self.assertEqual(len(input_list), len(mtx.inputList))
        for io in output_list:
            mtx.outputList.append(io)
        self.assertEqual(len(output_list), len(mtx.outputList))

        self.assertEqual(is_dummy, mtx.isDummy)
        self.assertFalse(mtx.isSigned)
        self.assertEqual(b"", mtx.raw())
        self.assertTrue(mtx.sign())
        self.assertEqual(expected_name, mtx.name)
        self.assertEqual(expected_data, mtx.raw().hex())
        self.assertEqual(excepted_raw_size, mtx.rawSize)
        self.assertEqual(excepted_virtual_size, mtx.virtualSize)

        self.assertEqual(
            sum(i["utxo"].amount for i in input_list),
            mtx.amount)
        self.assertEqual(
            sum(i["utxo"].amount for i in input_list)
            - sum(o["amount"] for o in output_list),
            mtx.feeAmount)
        return mtx

    def test_p2pkh(self) -> None:
        def input_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createInput(
                    self._coin,
                    "8878399d83ec25c627cfbf753ff9ca3602373eac437ab2676154a3c2da23adf3", # noqa
                    1,
                    private_key="L3jsepcttyuJK3HKezD4qqRKGtwc8d2d1Nw6vsoPDX9cMcUxqqMv", # noqa
                    address_type=self._coin.Address.Type.PUBKEY_HASH,
                    script_type=self._coin.Address.Script.Type.P2PKH,
                    amount=83727960,
                    sequence=0xfffffffe,
                    is_dummy=is_dummy)
            ]

        def output_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createOutput(
                    self._coin,
                    address_name="1N8QYQNAD8PLEJjmCGGR8iN1iuR9yXtY1x",  # noqa
                    amount=50000,
                    is_dummy=is_dummy),
                self._createOutput(
                    self._coin,
                    address_name="1ELReFsTCUY2mfaDTy32qxYiT49z786eFg",  # noqa
                    amount=83658760,
                    is_dummy=is_dummy)
            ]

        self._test_mtx(
            input_list(is_dummy=False),
            output_list(is_dummy=False),
            lock_time=0,
            is_dummy=False,
            expected_name="b8eab75158fc3f3bd8479005a02eef5a13c5d80e364ab155a4ebdb19d418b331",  # noqa
            expected_data=""
                "01000000018878399d83ec25c627cfbf753ff9ca3602373eac437ab2676154"  # noqa
                "a3c2da23adf3010000006b483045022100b167dd5c560454a8c7e6425aebde"  # noqa
                "647233110158acf84b1b81a9ed98b2c613a20220551d562999009596a0c1c1"  # noqa
                "2b2a77861cc9150bc77c025ed5309ff77d39bc889f0121033d5c2875c9bd11"  # noqa
                "6875a71a5db64cffcb13396b163d039b1d9327824891804334feffffff0250"  # noqa
                "c30000000000001976a914e7c1345fc8f87c68170b3aa798a956c2fe6a9eff"  # noqa
                "88ac0888fc04000000001976a91492461bde6283b461ece7ddf4dbf1e0a48b"  # noqa
                "d113d888ac00000000",  # noqa
            excepted_raw_size=226,
            excepted_virtual_size=226)

        self._test_mtx(
            input_list(is_dummy=True),
            output_list(is_dummy=True),
            lock_time=0,
            is_dummy=True,
            expected_name=None,
            expected_data=""
                "01000000018878399d83ec25c627cfbf753ff9ca3602373eac437ab2676154"  # noqa
                "a3c2da23adf3010000006b4800000000000000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000001210000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000feffffff0250"  # noqa
                "c30000000000001976a914e7c1345fc8f87c68170b3aa798a956c2fe6a9eff"  # noqa
                "88ac0888fc04000000001976a91492461bde6283b461ece7ddf4dbf1e0a48b"  # noqa
                "d113d888ac00000000",  # noqa
            excepted_raw_size=226,
            excepted_virtual_size=226)

    def test_p2pkh_uncompressed(self) -> None:
        def input_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createInput(
                    self._coin,
                    "01" * 32,
                    2,
                    private_key="5KHxtARu5yr1JECrYGEA2YpCPdh1i9ciEgQayAF8kcqApkGzT9s", # noqa
                    address_type=self._coin.Address.Type.PUBKEY_HASH,
                    script_type=self._coin.Address.Script.Type.P2PKH,
                    amount=1,
                    sequence=0xfffffffe,
                    is_dummy=is_dummy)
            ]

        def output_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createOutput(
                    self._coin,
                    address_name="1ExJJsNLQDNVVM1s1sdyt1o5P3GC5r32UG",  # noqa
                    amount=1,
                    is_dummy=is_dummy)
            ]

        self._test_mtx(
            input_list(is_dummy=False),
            output_list(is_dummy=False),
            lock_time=0,
            is_dummy=False,
            expected_name="5ea24fd0d01dda1994d4357efe38bb527279983e45cd6ad50dd0626b64234f83",  # noqa
            expected_data=""
                "01000000010101010101010101010101010101010101010101010101010101"  # noqa
                "010101010101020000008a473044022038b2497feeb5fb77c0f78594519040"  # noqa
                "c5400a108031596a607a96a2775a2ea79e02200b4b210ea49c6f222feadf21"  # noqa
                "a9f0bdc8b820b04ac60cf0ef8b62439d50c1c1690141043d5c2875c9bd1168"  # noqa
                "75a71a5db64cffcb13396b163d039b1d932782489180433476a4352a2add00"  # noqa
                "ebb0d5c94c515b72eb10f1fd8f3f03b42f4a2b255bfc9aa9e3feffffff0101"  # noqa
                "000000000000001976a914990ef60d63b5b5964a1c2282061af45123e93fcb"  # noqa
                "88ac00000000",  # noqa
            excepted_raw_size=223,
            excepted_virtual_size=223)

        self._test_mtx(
            input_list(is_dummy=True),
            output_list(is_dummy=True),
            lock_time=0,
            is_dummy=True,
            expected_name=None,
            expected_data=""
                "01000000010101010101010101010101010101010101010101010101010101"  # noqa
                "010101010101020000008b4800000000000000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000001410000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000000"  # noqa
                "0000000000000000000000000000000000000000000000000000feffffff01"  # noqa
                "01000000000000001976a914990ef60d63b5b5964a1c2282061af45123e93f"  # noqa
                "cb88ac00000000",  # noqa
            excepted_raw_size=224,
            excepted_virtual_size=224)

    # https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#native-p2wpkh # noqa
    def test_native_p2wpkh(self) -> None:
        def input_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createInput(
                    self._coin,
                    "fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f",  # noqa
                    0,
                    private_key="bbc27228ddcb9209d7fd6f36b02f7dfa6252af40bb2f1cbc7a557da8027ff866",  # noqa
                    address_type=self._coin.Address.Type.PUBKEY_HASH,
                    script_type=self._coin.Address.Script.Type.P2PK,
                    amount=625000000,
                    sequence=0xffffffee,
                    is_dummy=is_dummy),
                self._createInput(
                    self._coin,
                    "ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a",  # noqa
                    1,
                    private_key="619c335025c7f4012e556c2a58b2506e30b8511b53ade95ea316fd8c3286feb9",  # noqa
                    address_type=self._coin.Address.Type.WITNESS_V0_KEY_HASH,
                    script_type=self._coin.Address.Script.Type.P2WPKH,
                    amount=600000000,
                    sequence=0xffffffff,
                    is_dummy=is_dummy),
            ]

        def output_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createOutput(
                    self._coin,
                    address_name="1Cu32FVupVCgHkMMRJdYJugxwo2Aprgk7H",  # noqa
                    amount=112340000,
                    is_dummy=is_dummy),
                self._createOutput(
                    self._coin,
                    address_name="16TZ8J6Q5iZKBWizWzFAYnrsaox5Z5aBRV",  # noqa
                    amount=223450000,
                    is_dummy=is_dummy)
            ]

        self._test_mtx(
            input_list(is_dummy=False),
            output_list(is_dummy=False),
            lock_time=0x11,
            is_dummy=False,
            expected_name="e8151a2af31c368a35053ddd4bdb285a8595c769a3ad83e0fa02314a602d4609",  # noqa
            expected_data=""
                "01000000000102fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf4"  # noqa
                "33541db4e4ad969f00000000494830450221008b9d1dc26ba6a9cb62127b02"  # noqa
                "742fa9d754cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a"  # noqa
                "99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01eeffffffef51e1"  # noqa
                "b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a0100"  # noqa
                "000000ffffffff02202cb206000000001976a9148280b37df378db99f66f85"  # noqa
                "c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe"  # noqa
                "6a21b2d50ce2f0167faa815988ac000247304402203609e17b84f6a7d30c80"  # noqa
                "bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a0220573a954c451833"  # noqa
                "1561406f90300e8f3358f51928d43c212a8caed02de67eebee0121025476c2"  # noqa
                "e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee63571100"  # noqa
                "0000",  # noqa
            excepted_raw_size=343,
            excepted_virtual_size=261)

        self._test_mtx(
            input_list(is_dummy=True),
            output_list(is_dummy=True),
            lock_time=0x11,
            is_dummy=True,
            expected_name=None,
            expected_data=""
                "01000000000102fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf4"  # noqa
                "33541db4e4ad969f0000000049480000000000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000000"  # noqa
                "000000000000000000000000000000000000000000000001eeffffffef51e1"  # noqa
                "b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a0100"  # noqa
                "000000ffffffff02202cb206000000001976a9148280b37df378db99f66f85"  # noqa
                "c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe"  # noqa
                "6a21b2d50ce2f0167faa815988ac0002480000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000121000000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000011"  # noqa
                "000000",  # noqa
            excepted_raw_size=344,
            excepted_virtual_size=261)

    # https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#p2sh-p2wpkh
    def test_p2sh_p2wpkh(self) -> None:
        def input_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createInput(
                    self._coin,
                    "db6b1b20aa0fd7b23880be2ecbd4a98130974cf4748fb66092ac4d3ceb1a5477",  # noqa
                    1,
                    private_key="eb696a065ef48a2192da5b28b694f87544b30fae8327c4510137a922f32c6dcf",  # noqa
                    address_type=self._coin.Address.Type.WITNESS_V0_KEY_HASH,
                    script_type=self._coin.Address.Script.Type.P2SH_P2WPKH,
                    amount=1000000000,
                    sequence=0xfffffffe,
                    is_dummy=is_dummy)
                ]

        def output_list(*, is_dummy: bool) -> list[dict]:
            return [
                self._createOutput(
                    self._coin,
                    address_name="1Fyxts6r24DpEieygQiNnWxUdb18ANa5p7",  # noqa
                    amount=199996600,
                    is_dummy=is_dummy),
                self._createOutput(
                    self._coin,
                    address_name="1Q5YjKVj5yQWHBBsyEBamkfph3cA6G9KK8",  # noqa
                    amount=800000000,
                    is_dummy=is_dummy)
            ]

        self._test_mtx(
            input_list(is_dummy=False),
            output_list(is_dummy=False),
            lock_time=0x492,
            is_dummy=False,
            expected_name="ef48d9d0f595052e0f8cdcf825f7a5e50b6a388a81f206f3f4846e5ecd7a0c23",  # noqa
            expected_data=""
                "01000000000101db6b1b20aa0fd7b23880be2ecbd4a98130974cf4748fb660"  # noqa
                "92ac4d3ceb1a5477010000001716001479091972186c449eb1ded22b78e40d"  # noqa
                "009bdf0089feffffff02b8b4eb0b000000001976a914a457b684d7f0d539a4"  # noqa
                "6a45bbc043f35b59d0d96388ac0008af2f000000001976a914fd270b1ee6ab"  # noqa
                "caea97fea7ad0402e8bd8ad6d77c88ac02473044022047ac8e878352d3ebbd"  # noqa
                "e1c94ce3a10d057c24175747116f8288e5d794d12d482f0220217f36a485ca"  # noqa
                "e903c713331d877c1f64677e3622ad4010726870540656fe9dcb012103ad1d"  # noqa
                "8e89212f0b92c74d23bb710c00662ad1470198ac48c43f7d6f93a2a2687392"  # noqa
                "040000",  # noqa
            excepted_raw_size=251,
            excepted_virtual_size=170)

        self._test_mtx(
            input_list(is_dummy=True),
            output_list(is_dummy=True),
            lock_time=0x492,
            is_dummy=True,
            expected_name=None,
            expected_data=""
                "01000000000101db6b1b20aa0fd7b23880be2ecbd4a98130974cf4748fb660"  # noqa
                "92ac4d3ceb1a5477010000001716001479091972186c449eb1ded22b78e40d"  # noqa
                "009bdf0089feffffff02b8b4eb0b000000001976a914a457b684d7f0d539a4"  # noqa
                "6a45bbc043f35b59d0d96388ac0008af2f000000001976a914fd270b1ee6ab"  # noqa
                "caea97fea7ad0402e8bd8ad6d77c88ac024800000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000000"  # noqa
                "00000000000000000000000000000000000000000000000000000001210000"  # noqa
                "00000000000000000000000000000000000000000000000000000000000000"  # noqa
                "92040000",  # noqa
            excepted_raw_size=252,
            excepted_virtual_size=170)
