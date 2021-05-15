# JOK4
import random
from unittest import TestCase

from bmnclient.coins.coin_bitcoin import Bitcoin
from bmnclient.coins.hd import HdAddressIterator
from bmnclient.wallet import hd
from bmnclient.wallet.hd import HdNode

BIP32_TEST_VECTOR_1 = {
    "seed": "000102030405060708090a0b0c0d0e0f",
    "m": (
        "xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8",  # noqa
        "xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi"  # noqa
    ),
    "m/0H": (
        "xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw",  # noqa
        "xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7"  # noqa
    ),
    "m/0H/1": (
        "xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ",  # noqa
        "xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs"  # noqa
    ),
    "m/0H/1/2H": (
        "xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5",  # noqa
        "xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM"  # noqa
    ),
    "m/0H/1/2H/2": (
        "xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV", # noqa
        "xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334"  # noqa
    ),
    "m/0H/1/2H/2/1000000000": (
        "xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy",  # noqa
        "xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76"  # noqa
    )
}

BIP32_TEST_VECTOR_2 = {
    "seed": "fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542",  # noqa
    "m": (
        "xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB",  # noqa
        "xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U"  # noqa
    ),
    "m/0": (
        "xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH",  # noqa
        "xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt"  # noqa
    ),
    "m/0/2147483647H": (
        "xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a",  # noqa
        "xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9"  # noqa
    ),
    "m/0/2147483647H/1": (
        "xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon",  # noqa
        "xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef"  # noqa
    ),
    "m/0/2147483647H/1/2147483646H": (
        "xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL",  # noqa
        "xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc"  # noqa
    ),
    "m/0/2147483647H/1/2147483646H/2": (
        "xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt",  # noqa
        "xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j"  # noqa
    )
}

BIP32_TEST_VECTOR_3 = {
    "seed": "4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be",  # noqa
    "m": (
        "xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13",  # noqa
        "xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6"  # noqa
    ),
    "m/0H": (
        "xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y",  # noqa
        "xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L"  # noqa
    )
}

LEVELS_PATH_LIST = (
    ("", []),
    ("m", []),
    ("m/", []),
    ("m//", []),

    ("m/1/", [1]),
    ("/1/", [1]),
    ("1", [1]),
    ("m/1/2", [1, 2]),
    ("m/////1/////2////", [1, 2]),
    ("m/-1/2", [1 | 0x80000000, 2]),
    ("m/-1/2h", [1 | 0x80000000, 2 | 0x80000000]),
    ("m/-1/2h/3H", [1 | 0x80000000, 2 | 0x80000000, 3 | 0x80000000]),
    ("m/-1/2h/3H/4", [1 | 0x80000000, 2 | 0x80000000, 3 | 0x80000000, 4]),
    ("-1/2h/3H/4", [1 | 0x80000000, 2 | 0x80000000, 3 | 0x80000000, 4]),
    ("-1/2'/3H/4", [1 | 0x80000000, 2 | 0x80000000, 3 | 0x80000000, 4]),

    ("m/-1h/2h/3H/4", None),
    ("m/d", None),
    ("m/4294967295", [4294967295]),
    ("m/4294967296", None),
)


class TestHd(TestCase):
    def test_levels_path(self) -> None:
        for (s, r) in LEVELS_PATH_LIST:
            self.assertEqual(r, HdNode.levelsPathFromString(s))

    def test_bip32(self) -> None:
        test_list = (
            BIP32_TEST_VECTOR_1,
            BIP32_TEST_VECTOR_2,
            BIP32_TEST_VECTOR_3)
        for t in test_list:
            seed = bytes.fromhex(t["seed"])
            root_node = HdNode.deriveRootNode(seed)
            self.assertIsNotNone(root_node)

            for (path, keys) in t.items():
                if not path.startswith("m"):
                    continue
                node = root_node.fromLevelsPath(path)
                self.assertIsNotNone(node)
                self.assertEqual(
                    keys[0],
                    node.toExtendedKey(
                        Bitcoin.bip0032VersionPublicKey,
                        private=False))
                self.assertEqual(
                    keys[1],
                    node.toExtendedKey(
                        Bitcoin.bip0032VersionPrivateKey,
                        private=True))

    def test_hd_address_index(self) -> None:
        coin = Bitcoin()
        root_node = hd.HdNode.deriveRootNode(random.randbytes(64))
        coin.makeHdPath(root_node)

        for i in range(10):
            self.assertEqual(coin.nextHdIndex(0, False), i)
            coin.appendAddress(coin.createHdAddress(account=0, is_change=False))
            self.assertEqual(coin.nextHdIndex(0, False), i + 1)


class TestHdAddressIterator(TestCase):
    def setUp(self) -> None:
        root_node = HdNode.deriveRootNode(random.randbytes(64))
        self._purpose_node = root_node.deriveChildNode(44, hardened=True)

    def test(self) -> None:
        coin = Bitcoin()
        coin.makeHdPath(self._purpose_node)

        flush = 0
        append = 0
        it = None
        while flush < 1 or append < 0:
            it = HdAddressIterator(coin)
            flush = 0
            append = 0

            for address in it:
                if random.randint(0, 2) != 1:
                    flush += 1
                    it.markLastAddress(True)
                    # noinspection PyProtectedMember
                    self.assertGreater(
                        it._empty_address_counter[address.type],
                        0)
                else:
                    append += 1
                    it.markLastAddress(False)
                    # noinspection PyProtectedMember
                    self.assertEqual(
                        it._empty_address_counter[address.type],
                        0)
            self.assertRaises(StopIteration, next, it)

        self.assertIsNotNone(it)
        # noinspection PyProtectedMember
        self.assertEqual(len(it._empty_address_counter), 2)

        # noinspection PyProtectedMember
        for count in it._empty_address_counter.values():
            # noinspection PyProtectedMember
            self.assertGreater(count, it._EMPTY_ADDRESS_LIMIT)
