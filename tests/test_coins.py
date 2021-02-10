# JOK++
import unittest

from bmnclient.coins import Bitcoin
from bmnclient.coins.address import \
    BitcoinAddress, \
    BitcoinTestAddress, \
    LitecoinAddress
from bmnclient.language import Locale

BITCOIN_ADDRESS_LIST = (
    (
        "1PMycacnJaSqwwJqjawXBErnLsZ7RkXUAs",
        BitcoinAddress.Type.PUBKEY_HASH,
        0,
        "f54a5851e9372b87810a8e60cdd2e7cfd80b6e31"
    ), (
        "3Ps86GT6vHg7dCT5QhcECDFkRaUJbBzqXB",
        BitcoinAddress.Type.SCRIPT_HASH,
        5,
        "f33c134a48d70818bdc2cf09631316ce90f71366"
    ), (
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4",
        BitcoinAddress.Type.WITNESS_V0_KEY_HASH,
        0,
        "751e76e8199196d454941c45d1b3a323f1433bd6"
    ), (
        "bc1qeklep85ntjz4605drds6aww9u0qr46qzrv5xswd35uhjuj8ahfcqgf6hak",
        BitcoinAddress.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "cdbf909e935c855d3e8d1b61aeb9c5e3c03ae8021b286839b1a72f2e48fdba70"
    ), (
        "bc1sw50qa3jx3s",
        BitcoinAddress.Type.WITNESS_UNKNOWN,
        16,
        "751e"
    ), (
        "bc1gmk9yu",
        None,
        None,
        None
    ), (
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
        None,
        None,
        None
    )
)

BITCOIN_TEST_ADDRESS_LIST = (
    (
        "mxVFsFW5N4mu1HPkxPttorvocvzeZ7KZyk",
        BitcoinTestAddress.Type.PUBKEY_HASH,
        0x6f,
        "ba27f99e007c7f605a8305e318c1abde3cd220ac"
    ), (
       "n49mqVncWxMYwCmZDHXba3Y9RVPzAFTUoX",
       BitcoinTestAddress.Type.PUBKEY_HASH,
       0x6f,
       "f8496d9390c68a99b96e7c438af90f316739a839"
    ), (
        "2N7EFdToQVZviaVC2Wfkidm6HzntiqtVmDE",
        BitcoinTestAddress.Type.SCRIPT_HASH,
        0xc4,
        "9962b7013858273326d2e36057bde8c844f831a1"
    ), (
        "tb1qu03l73f3rdcjh0ywnhc8vc3yp5gumvgummhv7f",
        BitcoinTestAddress.Type.WITNESS_V0_KEY_HASH,
        0,
        "e3e3ff45311b712bbc8e9df07662240d11cdb11c"
    ), (
        "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",
        BitcoinTestAddress.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433"
    ), (
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",
        BitcoinTestAddress.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "1863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262"
    ), (
        "tb1s424qnvez45",
        BitcoinTestAddress.Type.WITNESS_UNKNOWN,
        16,
        "aaaa"
    ),
)

LITECOIN_ADDRESS_LIST = (
    (
        "LaMT348PWRnrqeeWArpwQPbuanpXDZGEUz",
        LitecoinAddress.Type.PUBKEY_HASH,
        0x30,
        "a5f4d12ce3685781b227c1f39548ddef429e9783"
    ), (
        "MQMcJhpWHYVeQArcZR3sBgyPZxxRtnH441",
        LitecoinAddress.Type.SCRIPT_HASH,
        0x32,
        "b48297bff5dadecc5f36145cec6a5f20d57c8f9b"
    ), (
        "ltc1q7nlrhuxks5rvc7aumcpzttm3xll3f5zqlp0pyv",
        LitecoinAddress.Type.WITNESS_V0_KEY_HASH,
        0,
        "f4fe3bf0d68506cc7bbcde0225af7137ff14d040"
    ), (
        "ltc1q5det08ke2gpet06wczcdfs2v3hgfqllxw28uln8vxxx82qlue6uswceljm",
        LitecoinAddress.Type.WITNESS_V0_SCRIPT_HASH,
        0,
        "a372b79ed9520395bf4ec0b0d4c14c8dd0907fe6728fcfccec318c7503fcceb9"
    )
)


class TestCoins(unittest.TestCase):
    def _test_address_decode(
            self,
            address_cls,
            address_list) -> None:
        for (address, type_, version, data) in address_list:
            a = address_cls.decode(address)
            if type_ is None:
                self.assertIsNone(a)
            else:
                self.assertIsNotNone(a)
                self.assertEqual(type_, a.type)
                self.assertEqual(version, a.version)
                self.assertEqual(data, a.data.hex())

    def test_address_decode(self) -> None:
        self._test_address_decode(
            BitcoinAddress,
            BITCOIN_ADDRESS_LIST)
        self._test_address_decode(
            BitcoinTestAddress,
            BITCOIN_TEST_ADDRESS_LIST)
        self._test_address_decode(
            LitecoinAddress,
            LITECOIN_ADDRESS_LIST)

    def test_string_to_amount(self) -> None:
        b = Bitcoin()

        for v in ("", "-", "+", "-.", "+.", "."):
            self.assertIsNone(b.stringToAmount(v))

        for v in ("--11", "++11", "-+11", "+-11", " 11", "11 ", "11. "):
            self.assertIsNone(b.stringToAmount(v))

        for (r, v) in (
                (0, "0"),
                (50 * b.decimalValue, "50"),
                (-50 * b.decimalValue, "-50"),
                (60 * b.decimalValue, "60."),
                (-60 * b.decimalValue, "-60."),

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

                (-92233720368 * b.decimalValue, "-92233720368"),
                (None, "-92233720369"),

                (92233720368 * b.decimalValue, "92233720368"),
                (None, "92233720369"),

                (92233720368 * b.decimalValue, "+92233720368"),
                (None, "+92233720369"),

                (-(2 ** 63), "-92233720368.54775808"),
                (None, "92233720369"),

                ((2 ** 63) - 1, "92233720368.54775807"),
                (None, "92233720368.54775808"),

                ((2 ** 63) - 1, "+92233720368.54775807"),
        ):
            self.assertEqual(r, b.stringToAmount(v))

    def test_string_to_amount_locale(self) -> None:
        b = Bitcoin()
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
            self.assertEqual(r, b.stringToAmount(v, locale=locale))

    def test_amount_to_string(self) -> None:
        b = Bitcoin()

        self.assertEqual("0", b.amountToString(0))
        self.assertEqual("-1", b.amountToString(-1 * 10 ** 8))
        self.assertEqual("1", b.amountToString(+1 * 10 ** 8))

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
            self.assertEqual("-" + d, b.amountToString(-s))
            self.assertEqual(d, b.amountToString(s))

        self.assertEqual(
            "92233720368.54775807",
            b.amountToString(9223372036854775807))
        self.assertEqual(
            "0",
            b.amountToString(9223372036854775808))
        self.assertEqual(
            "-92233720368.54775808",
            b.amountToString(-9223372036854775808))
        self.assertEqual(
            "0",
            b.amountToString(-9223372036854775809))
