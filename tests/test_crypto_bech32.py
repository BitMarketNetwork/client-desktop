from unittest import TestCase

from bmnclient.crypto.bech32 import Bech32

TEST_LIST = (
    (
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4",  # noqa
        "bc",
        0,
        "751e76e8199196d454941c45d1b3a323f1433bd6",  # noqa
    ),
    (
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7",  # noqa
        "tb",
        0,
        "1863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262",  # noqa
    ),
    (
        "bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7k7grplx",  # noqa
        "bc",
        1,
        "751e76e8199196d454941c45d1b3a323f1433bd6751e76e8199196d454941c45d1b3a323f1433bd6",  # noqa
    ),
    ("BC1SW50QA3JX3S", "bc", 16, "751e"),  # noqa
    (
        "bc1zw508d6qejxtdg4y5r3zarvaryvg6kdaj",  # noqa
        "bc",
        2,
        "751e76e8199196d454941c45d1b3a323",
    ),
    (
        "tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy",  # noqa
        "tb",
        0,
        "000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",  # noqa
    ),
    (
        "bc1qeklep85ntjz4605drds6aww9u0qr46qzrv5xswd35uhjuj8ahfcqgf6hak",  # noqa
        "bc",
        0,
        "cdbf909e935c855d3e8d1b61aeb9c5e3c03ae8021b286839b1a72f2e48fdba70",  # noqa
    ),
)


class TestBech32(TestCase):
    def test_encode(self) -> None:
        self.assertEqual(None, Bech32.encode("", 1, b"12"))
        self.assertEqual(None, Bech32.encode("", 1, b"1234"))
        self.assertEqual(None, Bech32.encode("", 1, b"1234"))
        self.assertEqual(
            "f1pxyerxdql9k5af", Bech32.encode("f", 1, b"1234")  # noqa
        )
        self.assertEqual(
            "f1qxyerxdqz6k94r",  # noqa
            Bech32.encode("f", 0, b"1234"),
        )
        self.assertEqual(
            "f1sxyerxdqhxk0c8", Bech32.encode("f", 16, b"1234")  # noqa
        )
        self.assertEqual(None, Bech32.encode("f", 17, b"1234"))
        self.assertEqual("a1q3g6mn3", Bech32.encode("a", 0, b""))
        self.assertEqual(
            "bc1qlud2hqlk", Bech32.encode("bc", 0, b"\xff")  # noqa
        )
        self.assertEqual("bc12gny8wv", Bech32.encode("bc", 10, b""))

        self.assertEqual(
            "f1qxyerxdp4xcmnswfsj7r2mj",  # noqa
            Bech32.encode("f", 0, b"1234567890" * 1),
        )
        self.assertEqual(
            "f1qxyerxdp4xcmnswfsxyerxdp4xcmnswfsg544fr",  # noqa
            Bech32.encode("f", 0, b"1234567890" * 2),
        )

        for address, hrp, version, value in TEST_LIST:
            self.assertEqual(
                address.lower(),
                Bech32.encode(hrp, version, bytes.fromhex(value)).lower(),
            )

    def test_decode(self) -> None:
        result_none = (None, None, None)

        self.assertEqual(result_none, Bech32.decode("12gny8wv"))
        self.assertEqual(result_none, Bech32.decode("bc1"))
        self.assertEqual(result_none, Bech32.decode("bc1_BAD_CHAR"))
        self.assertEqual(
            ("f", 16, b"1234"), Bech32.decode("f1sxyerxdqhxk0c8")
        )  # noqa
        self.assertEqual(("a", 0, b""), Bech32.decode("a1q3g6mn3"))
        self.assertEqual(
            ("f", 0, b"1234567890" * 1),
            Bech32.decode("f1qxyerxdp4xcmnswfsj7r2mj"),
        )  # noqa

        for address, hrp, version, value in TEST_LIST:
            self.assertEqual(
                (hrp, version, bytes.fromhex(value)), Bech32.decode(address)
            )
