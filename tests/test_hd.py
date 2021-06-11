# JOK4
from __future__ import annotations

from os import urandom
from random import randint
from typing import TYPE_CHECKING
from unittest import TestCase

from bmnclient.coins.coin_bitcoin import Bitcoin
from bmnclient.coins.hd import HdAddressIterator, HdNode

if TYPE_CHECKING:
    from typing import Final

BIP32_TEST_VECTOR_1: Final = {
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

BIP32_TEST_VECTOR_2: Final = {
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

BIP32_TEST_VECTOR_3: Final = {
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

HARDENED: Final = 0x80000000

PATH_LIST: Final = (
    ("", (tuple(), False)),
    ("m", (tuple(), True)),
    ("m/", (tuple(), True)),
    ("m//", (tuple(), True)),

    ("m/1/", ((1, ), True)),
    ("/1/", ((1, ), False)),
    ("1", ((1, ), False)),
    ("m/1/2", ((1, 2), True)),
    ("m/////1/////2////", ((1, 2), True)),
    ("m/-1/2", ((1 | HARDENED, 2), True)),
    ("m/-1/2h", ((1 | HARDENED, 2 | HARDENED), True)),
    ("m/-1/2h/3H", ((1 | HARDENED, 2 | HARDENED, 3 | HARDENED), True)),
    ("m/-1/2h/3H/4", ((1 | HARDENED, 2 | HARDENED, 3 | HARDENED, 4), True)),
    ("-1/2h/3H/4", ((1 | HARDENED, 2 | HARDENED, 3 | HARDENED, 4), False)),
    ("-1/2'/3H/4", ((1 | HARDENED, 2 | HARDENED, 3 | HARDENED, 4), False)),

    ("m/-1h/2h/3H/4", (None, False)),
    ("m/d", (None, False)),
    ("m/4294967295", ((4294967295, ), True)),
    ("m/4294967296", (None, False)),
)

# data from https://iancoleman.io/bip39/
PUBLIC_KEY_ROOT_SEED: Final = "a7d4b121dd7240b4122509060da1acdcd55d85ab09d5c6249e8d2cf530142ab8b0b99b511c8ab3778a6e62f8c7fdf3524eb7fddab29aa49a5329bf1aa3d403e6"  # noqa
PUBLIC_KEY_PATH_LIST: Final = {
    "m/0": "xpub69PLnHQACW9e7DpECfkdGpqk7h4Z9M8MdGgYSQEjVYHFRzpYqshxRTAZWrKGt8XJhqrfYbYC1JURDjevFUNpk51mta38EbMbN4qDHm26f61",  # noqa
    "m/0/1": "xpub6AUip5vufjmgE6oDSoAXswSKsHG8ABr5AxNedpnBiuJW64xrurc7CaY1gwGLJ4PMds2VnssFFexPnT1GvxE5YEeC5oR6Cag9bMNMphBJxPM",  # noqa
    "m/0/1/2": "xpub6CRz7SMHQTHEgHFq5whoNpvs9Rf3gTfCsoFtFB8Nipjf3ATPdGJ6GvqNthbRyp8iqnPEWZUfWiFtiUk6wGduCW3zEcGFtkCqYS21hqwM6Au", # noqa
    "m/0/1/2/3": "xpub6EJR9VYp4YKnyFtsVjrtJ2BXaFDzFXgDrTtn9QwTYeJM2rB2RMdNcte54JrPEomKY8AB2XJEYuqmP6Ty9nQCegRuvmbxXFpx4cZRPGapgUv",  # noqa
    "m/0/1/2/3/4/5": "xpub6JELTtwmGq9eMz8RMKCEgyGNeiydWYVVK6GyNyp45s4pspiM6n2W2xxomE6Lqox86Pe4VwzLMfoSakr5CxchY9RkDdg21xMvtr2474o5q8p",  # noqa
    "m/5": "xpub69PLnHQACW9eHy3pM678VstoZAke9ioaxDtSafz42375VPs24P7dw3gzGTjeQ8i1tBYoxic8VQYUmRHhy6wLGAYAmLURAAiDGGMPsycGmf5",  # noqa
    "m/5/4": "xpub6ALK4QJGfad6hKcdDmA3JsZ1GcPUeXnwFva6RGVWuefp1CS6eSVC6krcw5iAjQbbTKgGMNnpWgX1Pvv61zUtbF4R28DBjhJx8pLZGdHXBve",  # noqa
    "m/5/4/3": "xpub6CvLsvdDDbUXn6NxgPdzHfbe1afg8V8npCS7teWaDsFA1WVvWT1g8pdd7U5zEMmybb9ngpJAukaWLtwyfCE1hBqqCKmZzbUBLUJZzQZ3EDk",  # noqa
    "m/5/4/3/2": "xpub6DjXp4LW8ZYq4S2hZsXfAKjWrjVdpALCdPDYirWtaJFEaw2M7yJ46UAjpcNeATWezoadLJegySUWuTmpshsSigMvx4B3wEVbGt37i3ezGnG",  # noqa
    "m/5/4/3/2/1": "xpub6FSGCME7EqcZayAiGM4tmbtJrJcedMegqvsB9tvFSN9cy5XPTCcKKcpYfJdCEtokcpJUFaoEsDMqGMKKP9RZHtKfhVPXR1UbQGLEfGpajiz",  # noqa
    "m/5/4/3/2/1/0": "xpub6JW8M2XwLsRLaecwaxKx6xXHmFx4Bt5KeCim5QgjuErEtVv2yZv7UgrTyWoYM9xvz5CsqtfncQiadWqYaCcSQMFUjsPRVd789RxzkJUKZ7m",  # noqa
}


class TestHd(TestCase):
    def test_path(self) -> None:
        for (s, r) in PATH_LIST:
            self.assertEqual(r, HdNode.pathFromString(s))

    def _assertKeys(
            self,
            node: HdNode,
            excepted_public_key: str,
            excepted_private_key: str) -> None:
        self.assertIsNotNone(node)
        self.assertEqual(
            excepted_public_key,
            node.toExtendedKey(
                Bitcoin.bip0032VersionPublicKey,
                private=False))

        version, node2 = HdNode.fromExtendedKey(excepted_public_key)
        self.assertEqual(Bitcoin.bip0032VersionPublicKey, version)
        self.assertIsNotNone(node2)
        self.assertEqual(node.depth, node2.depth)
        self.assertEqual(node.index, node2.index)
        self.assertEqual(
            excepted_public_key,
            node2.toExtendedKey(
                Bitcoin.bip0032VersionPublicKey,
                private=False))

        if not node.depth:
            self.assertEqual(0, node2.index)
            self.assertEqual("m", node2.pathToString())
        elif node.depth == 1:
            self.assertTrue(node2.pathToString().startswith("m/"))
            self.assertEqual(2, len(node2.pathToString().split("/")))
        else:
            self.assertFalse(node2.pathToString().startswith("m"))
            self.assertEqual(1, len(node2.pathToString().split("/")))

        if node.privateKey is None:
            return

        self.assertEqual(
            excepted_private_key,
            node.toExtendedKey(
                Bitcoin.bip0032VersionPrivateKey,
                private=True))

        version, node2 = HdNode.fromExtendedKey(excepted_private_key)
        self.assertEqual(Bitcoin.bip0032VersionPrivateKey, version)
        self.assertIsNotNone(node2)
        self.assertEqual(
            excepted_private_key,
            node2.toExtendedKey(
                Bitcoin.bip0032VersionPrivateKey,
                private=True))

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
                node = root_node.fromPath(path, private=True)
                self._assertKeys(node, keys[0], keys[1])
                self.assertEqual(path, node.pathToString())

                version, node = HdNode.fromExtendedKey(keys[1])
                self.assertEqual(Bitcoin.bip0032VersionPrivateKey, version)
                self._assertKeys(node, keys[0], keys[1])

                path, is_full_path = HdNode.pathFromString(path)
                self.assertIsNotNone(path)
                self.assertTrue(is_full_path)
                if not path:
                    continue
                node = root_node.fromPath(path[:-1], private=True)
                self.assertIsNotNone(node)
                self.assertIsNotNone(node.privateKey)
                node = node.deriveChildNode(
                    HdNode.fromHardenedLevel(path[-1]),
                    hardened=HdNode.isHardenedLevel(path[-1]),
                    private=False)
                self._assertKeys(node, keys[0], keys[1])

    def test_derive_public_key(self) -> None:
        seed = bytes.fromhex(PUBLIC_KEY_ROOT_SEED)
        root_node = HdNode.deriveRootNode(seed)
        self.assertIsNotNone(root_node)

        # public -> public
        for (path, value) in PUBLIC_KEY_PATH_LIST.items():
            node = root_node.fromPath(path, private=False)
            self.assertIsNotNone(node)
            self.assertEqual(path, node.pathToString())
            self.assertEqual(
                value,
                node.toExtendedKey(
                    Bitcoin.bip0032VersionPublicKey,
                    private=False))

        # private -> public
        for (path, value) in PUBLIC_KEY_PATH_LIST.items():
            path, _ = HdNode.pathFromString(path)
            self.assertIsNotNone(path)
            for i in range(2, 10):
                if len(path) < i:
                    continue
                node = root_node.fromPath(path[:-i], private=True)
                self.assertIsNotNone(node)

                node = node.fromPath(path[-i:], private=False)
                self.assertIsNotNone(node)
                self.assertEqual(
                    value,
                    node.toExtendedKey(
                        Bitcoin.bip0032VersionPublicKey,
                        private=False))

    def test_hd_address_index(self) -> None:
        coin = Bitcoin()
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)
        purpose_node = root_node.deriveChildNode(3, hardened=True, private=True)
        self.assertIsNotNone(purpose_node)
        self.assertTrue(coin.deriveHdNode(purpose_node))

        for account in range(0, 10):
            for is_change in (False, True):
                for i in range(10):
                    change = 1 if is_change else 0
                    self.assertEqual(coin.nextHdIndex(account, change), i)
                    address = coin.deriveHdAddress(
                        account=account,
                        is_change=is_change)
                    self.assertIsNotNone(address)
                    coin.appendAddress(address)
                    self.assertEqual(coin.nextHdIndex(account, change), i + 1)


class TestHdAddressIterator(TestCase):
    def setUp(self) -> None:
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)
        self._purpose_node = root_node.deriveChildNode(
            44,
            hardened=True,
            private=True)
        self.assertIsNotNone(self._purpose_node)

    def test(self) -> None:
        coin = Bitcoin()
        self.assertTrue(coin.deriveHdNode(self._purpose_node))

        flush = 0
        append = 0
        while flush < 1 or append < 1:
            it = HdAddressIterator(coin)
            flush = 0
            append = 0

            for _ in it:
                if not 0 < randint(0, 10) < 2:
                    flush += 1
                    it.markCurrentAddress(True)
                    # noinspection PyProtectedMember
                    self.assertLess(0, it._empty_address_count)
                else:
                    append += 1
                    it.markCurrentAddress(False)
                    # noinspection PyProtectedMember
                    self.assertEqual(0, it._empty_address_count)
