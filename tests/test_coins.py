# JOK4
from __future__ import annotations

from os import urandom
from random import randint
from typing import TYPE_CHECKING
from unittest import TestCase

from bmnclient.coins.coin_bitcoin import Bitcoin, BitcoinTest
from bmnclient.coins.coin_litecoin import Litecoin
from bmnclient.coins.hd import HdNode
from bmnclient.language import Locale

if TYPE_CHECKING:
    from typing import Iterable
    from bmnclient.coins.abstract.coin import AbstractCoin


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


class TestCoins(TestCase):
    def _test_address_decode(
            self,
            coin: AbstractCoin,
            address_list: Iterable[tuple]) -> None:
        hash_check_count = 0

        # noinspection PyUnusedLocal
        for (address, type_, version, hash_) in address_list:
            address = coin.Address.decode(coin, name=address)
            if type_ is None:
                self.assertIsNone(address)
            else:
                self.assertIsNotNone(address)
                self.assertEqual(type_, address.type)
                if hash_ and len(hash_) == type_.value.size * 2:
                    self.assertEqual(hash_, address.hash.hex())
                    hash_check_count += 1
                else:
                    self.assertEqual(b"", address.hash)
        self.assertTrue(hash_check_count > 0)

    def test_address_decode(self) -> None:
        self._test_address_decode(
            Bitcoin(),
            BITCOIN_ADDRESS_LIST)
        self._test_address_decode(
            BitcoinTest(),
            BITCOIN_TEST_ADDRESS_LIST)
        self._test_address_decode(
            Litecoin(),
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
            coin = Bitcoin()
            for i in range(limit):
                address = coin.Address(
                    coin,
                    name="address_{:06d}".format(i),
                    type_=coin.Address.Type.UNKNOWN)
                self.assertTrue(coin.appendAddress(address))

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
                address = coin.Address(
                    coin,
                    name="address_new_{:06d}".format(i),
                    type_=coin.Address.Type.UNKNOWN)
                self.assertTrue(coin.appendAddress(address))

                mempool_list = coin.createMempoolAddressLists(limit)
                # noinspection PyProtectedMember
                self.assertEqual(len(coin._mempool_cache), len(mempool_list))

    def test_serialization(self) -> None:
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)

        purpose_node = root_node.deriveChildNode(
            44,
            hardened=True,
            private=True)
        self.assertIsNotNone(purpose_node)

        coin = Bitcoin()
        self.assertTrue(coin.deriveHdNode(purpose_node))
        coin.height = randint(1000, 100000)
        coin.offset = "offset" + str(randint(1000, 100000))
        coin.unverifiedOffset = "u_offset" + str(randint(1000, 100000))
        coin.unverifiedHash = "u_hash" + str(randint(1000, 100000))
        coin.verifiedHeight = randint(1000, 100000)

        for address_index in range(1, 3):
            address = coin.deriveHdAddress(
                account=0,
                is_change=False,
                amount=randint(1000, 100000),
                tx_count=randint(1000, 100000),
                label="address label " + str(address_index),
                comment="address comment " + str(address_index),
                history_first_offset="first_" + str(randint(1000, 100000)),
                history_last_offset="last_" + str(randint(1000, 100000)))
            self.assertIsNotNone(address)

            input_list = []
            for i in range(1, 3):
                input_list.append(coin.Tx.Io(
                    coin,
                    output_type="output_type_" + str(i),
                    address_name=address.name,
                    amount=randint(1000, 100000)))

            output_list = []
            for i in range(1, 3):
                output_list.append(coin.Tx.Io(
                    coin,
                    output_type="output_type_" + str(i),
                    address_name=address.name,
                    amount=randint(1000, 100000)))
            output_list.append(coin.Tx.Io(
                coin,
                output_type="output_type_nulldata",
                address_name=None,
                amount=0))

            for i in range(1, 4):
                address.appendTx(coin.Tx(
                    coin,
                    name="tx_name_" + str(i),
                    height=randint(10000, 1000000),
                    time=randint(10000, 1000000),
                    amount=randint(10000, 1000000),
                    fee_amount=randint(10000, 1000000),
                    coinbase=randint(0, 1) == 1,
                    input_list=input_list,
                    output_list=output_list))

            address.utxoList = [coin.Tx.Utxo(
                coin,
                name="utxo_" + str(i),
                height=randint(10000, 1000000),
                index=randint(10000, 1000000),
                amount=randint(10000, 1000000)) for i in range(1, 3)]

            coin.appendAddress(address)

        data = coin.serialize()
        self.assertIsInstance(data, dict)

        # from pprint import pprint
        # pprint(data, sort_dicts=False)

        coin_new = Bitcoin()
        Bitcoin.deserialize(coin_new, **data)

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
            self.assertEqual(a1.name, a2.name)
            self.assertEqual(a1.exportKey(), a2.exportKey())
            self.assertEqual(a1.amount, a2.amount)
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
                self.assertEqual(t1.coinbase, t2.coinbase)

                # io list compare
                self.assertEqual(len(t1.inputList), len(t2.inputList))
                self.assertEqual(len(t1.outputList), len(t2.outputList))
                for io_index in range(len(t1.inputList)):
                    io1 = t1.inputList[io_index]
                    io2 = t2.inputList[io_index]
                    self.assertEqual(io1.outputType, io2.outputType)
                    self.assertEqual(io1.address.name, io2.address.name)
                    self.assertEqual(io1.address.amount, io2.address.amount)
                for io_index in range(len(t1.outputList)):
                    io1 = t1.outputList[io_index]
                    io2 = t2.outputList[io_index]
                    self.assertEqual(io1.outputType, io2.outputType)
                    self.assertEqual(io1.address.name, io2.address.name)
                    self.assertEqual(io1.address.amount, io2.address.amount)

            # utxo list compare
            self.assertEqual(len(a1.utxoList), len(a2.utxoList))
            for utxo_index in range(len(a1.utxoList)):
                u1 = a1.utxoList[utxo_index]
                u2 = a2.utxoList[utxo_index]
                self.assertEqual(u1.name, u2.name)
                self.assertEqual(u1.height, u2.height)
                self.assertEqual(u1.index, u2.index)
                self.assertEqual(u1.amount, u2.amount)
