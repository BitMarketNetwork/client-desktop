from __future__ import annotations

from os import urandom
from random import randint
from typing import TYPE_CHECKING
from unittest import TestCase

from bmnclient.coins.coin_bitcoin import Bitcoin
from bmnclient.coins.hd import HdAddressIterator, HdNode
from tests.helpers import TestCaseApplication

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


class TestHd(TestCaseApplication):
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
        coin = Bitcoin(model_factory=self._application.modelFactory)
        self.assertTrue(coin.save())

        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)
        self.assertTrue(coin.deriveHdNode(root_node))

        purpose = coin.Address.Type.DEFAULT.value.hdPurpose
        for account in range(0, 10):
            for is_change in (False, True):
                for i in range(10):
                    change = 1 if is_change else 0
                    self.assertEqual(
                        i,
                        coin.nextHdIndex(purpose, account, change))
                    address = coin.deriveHdAddress(
                        account=account,
                        is_change=is_change)
                    self.assertIsNotNone(address)
                    self.assertTrue(address.save())
                    self.assertEqual(
                        i + 1,
                        coin.nextHdIndex(purpose, account, change))


# https://iancoleman.io/bip39/
HD_ADDRESS_LIST = (
    {
        "seed": "123be674f6d2074e37b6621795a33a2bc967ffcf24a40c2a87a1410d4bff08777520d13d8fe6ae3c41dc7bd722e3dfbbbf5c0c5a39340d68642006a324ccec6f",  # noqa

        # m/84'/0'/0'/0
        "m/84'/0'/0'/0/0": (
            "bc1qv2eet9m0py0g7aftpzx44fcwtww78nh4npcdtj",  # noqa
            "0263bd2afff941b8a3276b5ac550e9b6c80728014e97a5aee16e7ac3a67969a04a"  # noqa
        ),
        "m/84'/0'/0'/0/1": (
            "bc1qclhl7jknfrkxrfjpcdkw2f8wvdkw8h66dyd55g",  # noqa
            "02f471d882da3debb7a814c4296b0466ee783b063a4095171073c85b53607615db"  # noqa
        ),
        "m/84'/0'/0'/0/2": (
            "bc1qd5m7kjscvd6vf3exk24nzgrt7py0ygxx9ysf6g",  # noqa
            "02807d91da39216ea9918c54859e8ed43cad1802311f32ac521d6412e99783ed24"  # noqa
        ),
        "m/84'/0'/0'/0/3": (
            "bc1ql6l4vy6utwp4ug0uzu05c2050mlg9f6dgwg8cg",  # noqa
            "0352891de10dd1516914c6e006f1234f7aeb528894c1b1777e60a2fe09a972b36e"  # noqa
        ),
        "m/84'/0'/0'/0/4": (
            "bc1qcegxwka86gws9kussnqemjr843h7jkd6q6zvnw",  # noqa
            "02d6d564271215a074b329df7c13671bbbe4acc5b12f6dedd6e743c32569fd6dce"  # noqa
        ),
        "m/84'/0'/0'/0/5": (
            "bc1qwylqm0vp5rnxvwnq7394n2j82kx4h3809pn489",  # noqa
            "02f7a5ef8aa3cee31c1c0011f2252990fb46aa6125ba8b436891670399107e2333"  # noqa
        ),

        # m/84'/0'/1'/0
        "m/84'/0'/1'/0/0": (
            "bc1q2t845rff2hzx66nhdjmsxryxpaflh68tk7rzx5",  # noqa
            "02f97d5f119afae3ac9b5c53313e368de7dc6fb0e8e125cfe3dca76ee9a1f21df6"  # noqa
        ),
        "m/84'/0'/1'/0/1": (
            "bc1qzdunnmmpahvnfpe6lkhyehvplm2td0k8h6t9e7",  # noqa
            "033b5bd0f2521f3e4db045e9e307cd77bbf1f5162cfd6cc0da7aa542b845a4475b"  # noqa
        ),
        "m/84'/0'/1'/0/2": (
            "bc1qkssyf2mjyd5cnsdjm9cqsyg5f2jplxg8a2da02",  # noqa
            "03ac0fe46c0b412b24ec3e2e711d071dc59782b8d02a84c223f46dbdcc2060cf50"  # noqa
        ),
        "m/84'/0'/1'/0/3": (
            "bc1q7rmezld3dvj0mq9m5gpxcwrsnflqq0w43a7psq",  # noqa
            "02ea9727ad6d577f513400eb41a8513c94bb71dc6d2c5e7c53cd0af10d5afe1976"  # noqa
        ),
        "m/84'/0'/1'/0/4": (
            "bc1qtd0qg4mawund5dckusa08nq564xvhtt4e92r6j",  # noqa
            "021c7f2ae27027d87d76bf604b8e82f19625bb5d17224ffabe63ceea6e8d931bdd"  # noqa
        ),
        "m/84'/0'/1'/0/5": (
            "bc1qwfdhqxecdz2uy7z5rrcmtfrn3gywqljug0fm8d",  # noqa
            "03f410f4f2352d0d73ef4d6ac4bc99badbccfd046b047243b46e268adf785d6ff2"  # noqa
        ),

        # m/84'/0'/0'/1
        "m/84'/0'/0'/1/0": (
            "bc1qvqhg5un7rvnt88y87h4yvnl7u95fsmxdh3qf7x",  # noqa
            "0205cf834e36521b19c730e9ad3ed085cc3091c5bb567730370e9db896ba48fed5"  # noqa
        ),
        "m/84'/0'/0'/1/1": (
            "bc1qxlhywz2aeds6qs8wqdlvhfw0wkqhvfnmkld7q8",  # noqa
            "022c429045a000c56229b1388c2cc9a285d9d4c411bc0714cf12cdcfdd0bc9d06f"  # noqa
        ),
        "m/84'/0'/0'/1/2": (
            "bc1qghxtqx9dkjj0phezkcrgely5nu4tan0ek89p8v",  # noqa
            "02664a5144bfaab44ea382747a8baf8b24e1532bcfe01658039071e8d75d63beaf"  # noqa
        ),
        "m/84'/0'/0'/1/3": (
            "bc1q9zsuy253mc30hlf8z77kx6gp9e3n5ntqy9ufmx",  # noqa
            "03b68113faa1f283bb58766dd4c3a142f159a0686cf45b4c0c6c0b4ac401649fa0"  # noqa
        ),
        "m/84'/0'/0'/1/4": (
            "bc1qmqk7my37w87c3x9hg36d2q4u2pr9vrm8tnw7gd",  # noqa
            "03550081113163fdb19672d77178654345a84f866012176a50533b69c5d214fd4f"  # noqa
        ),
        "m/84'/0'/0'/1/5": (
            "bc1qed05594uqd0eec5ww9fyaexkhlxl396xh002qp",  # noqa
            "031e52fc136d0fe767c0f8cf134ca629234ee28229b48f522c38fdfe99d8a93125"  # noqa
        ),

        # m/84'/0'/1'/1
        "m/84'/0'/1'/1/0": (
            "bc1qlys8dctlyuk34rv3q2dtrnjfczwrfhrfy6nqcu",  # noqa
            "024f743ba82d63b4e49a6c869767949f0074fbcf7729f566a83cc0123e467296f2"  # noqa
        ),
        "m/84'/0'/1'/1/1": (
            "bc1q5ehpjy8mxxf33mnpx73ut46dhjljff4g8m7h4g",  # noqa
            "03da025913e5571b80747f6a2ae752c7826fae8ff96faac6746f1b40f0e33b9c96"  # noqa
        ),
        "m/84'/0'/1'/1/2": (
            "bc1q8wfcrjg04xdgx4auxkg89u6dllf2rppkuwh5ka",  # noqa
            "03afcae7dd33ed4ca93d37586fed028fb35771526807f0b97d195d793c999c34b2"  # noqa
        ),
        "m/84'/0'/1'/1/3": (
            "bc1qqzdvv2ywxn89l3x7qvuc26033v8yfn93qklgu4",  # noqa
            "0376fa5fca39eed1edc5511e82c1db142c338c55ec1e0822a3517d3be53bfb6f76"  # noqa
        ),
        "m/84'/0'/1'/1/4": (
            "bc1qsctyenjtvaq59glgkxf8q0zvaa6luw82yfahxm",  # noqa
            "0361c058cfe49c0d6e77efa3292aa5f4ae04d08b621d40e3c16be471462dce7be9"  # noqa
        ),
        "m/84'/0'/1'/1/5": (
            "bc1qkt5gr08jhl6rxpemsmhu77vkmftxxes30dfe5h",  # noqa
            "032db8487d7ca46dd907807e7f19a8580f5e9ff5e22509f7664b84e0fd841d17d7"  # noqa
        ),

        # m/44'/0'/0'/0
        "m/44'/0'/0'/0/0": (
            "1PtRP5nQWPAFFYWHs5Q2h94wM9n5P63t19",  # noqa
            "03bf80699f17f18c5d1c62bac4047a3cb0ced7cda315be89ff9ac2b50d6204558c"  # noqa
        ),
        "m/44'/0'/0'/0/1": (
            "19sVkPzjGhGFg8A6ehoNSCKj8JHfA3YHUg",  # noqa
            "03ebb3ac9b223de9206ea32a861f60648166964a671eca7d1b88f6b7d05d2e6bc7"  # noqa
        ),
        "m/44'/0'/0'/0/2": (
            "1EJYTo9ju5kfY6DiLkAXKsFRqidVe66U67",  # noqa
            "03e295e0c7375e0e52b08d9c588152f650337512d2a262f9a0f8f9d772b24bdb77"  # noqa
        ),
        "m/44'/0'/0'/0/3": (
            "1EjbW4y17YJdxS24rbDCi9PU9EiJKq4euX",  # noqa
            "0360b2214d3a9ff1008857985d3921f84d8cc7fe7a824fa45f6d7d576dc9b43842"  # noqa
        ),
        "m/44'/0'/0'/0/4": (
            "16WRz9bqYTMkEAvvED4d4vMiXtHXfgp6Gm",  # noqa
            "027c08b788e61fdcb308cc7b4687559a2fa3c5d75a2bb09988d440b39acce83042"  # noqa
        ),
        "m/44'/0'/0'/0/5": (
            "1P4eqAbpcozUQK8B1Kioodu2meS69mjg4B",  # noqa
            "0322252e2780be00350d99b3f2daecc06dd36e642abe6e1c81b630d61b1d9e9211"  # noqa
        ),

        # m/44'/0'/1'/0
        "m/44'/0'/1'/0/0": (
            "1Mb3R3Pm1To6i77px3oZF7ZrPW4KvCR65b",  # noqa
            "02a8e2ea462653d0646460fe5db57ed6248a4411e4a5d7fa72cf2b910b27ec40a1"  # noqa
        ),
        "m/44'/0'/1'/0/1": (
            "1inLbRfuMiaviwXjL8tfARNuhdsFtYsfN",  # noqa
            "021bbb3ad8f52de427ec0557972a614c0af785986738e942efa09dfc8f92c3892d"  # noqa
        ),
        "m/44'/0'/1'/0/2": (
            "13gZmE6YggsM1PXDdpuJGVzvub8sWfTXaz",  # noqa
            "03f7459e1db4ca1820e797ec0a163b6cd92ca185ab26819afe007c024804921810"  # noqa
        ),
        "m/44'/0'/1'/0/3": (
            "17NjYyZN8UXXmPb9bYxcoFsS1zLMdtnbNA",  # noqa
            "037524656ca20b8f2526c46795523aa812e086f322a0d58ac442ff65f3fa960dd8"  # noqa
        ),
        "m/44'/0'/1'/0/4": (
            "1BPFub9RSKiZ9uovRCYhxwr6DH4jDWeNQR",  # noqa
            "034fcb0980b73a1edd50b1340def1449227a889a080440ac121de0604beacca894"  # noqa
        ),
        "m/44'/0'/1'/0/5": (
            "18tNKZ35f4kjEDaoramjuraXqAfmMFpG7u",  # noqa
            "02970f6105191add12604c737566f2c46140bb611c417e2091ed27127c33a327da"  # noqa
        ),

        # m/44'/0'/0'/1
        "m/44'/0'/0'/1/0": (
            "1BRT3zJr63Hu4jAnRqzaJgFTLJGatmG4Xz",  # noqa
            "03c3beae5512516db9f1b0f1776c7df2b9b7885c02a505ed3e59b826614f9d051b"  # noqa
        ),
        "m/44'/0'/0'/1/1": (
            "1MjNrcs89p4zmFpg52XNoFWihr1ivCdkbB",  # noqa
            "031c2f0d9a3553abff33cb9308c90051c02903ba6bbbb9acce4d26f262023591e8"  # noqa
        ),
        "m/44'/0'/0'/1/2": (
            "18uKAmWRSjdCK5RhcNpF8VaMAbTxeJsLks",  # noqa
            "032e3abf065a0569f0a21ede1f91bbc280d6a8383a79f9d75fea9500e790731ca9"  # noqa
        ),
        "m/44'/0'/0'/1/3": (
            "1KwZpc9tWWjKqJ9mK9p5ntZvyky7NgCqqG",  # noqa
            "03e6ab8946dabe5c4cc2534c65c554588639e89ea03ac0ffa32e0ce10c1fd960a5"  # noqa
        ),
        "m/44'/0'/0'/1/4": (
            "19vnqkMsss2MsSvjo3NxjShvcb5Ma7pAkg",  # noqa
            "039c04ee5f599309a1230f67547f37cd7542aa5da74f7b0759d540fa065adb1bb1"  # noqa
        ),
        "m/44'/0'/0'/1/5": (
            "1JprMNW16gUVfa6q53JWMxUd2rD5QQbQ6k",  # noqa
            "02fa07361b0ef3fffda0d896155a4c666f00d462d32fd94a44e1ca8cbf64ee9730"  # noqa
        ),

        # m/44'/0'/1'/1
        "m/44'/0'/1'/1/0": (
            "1N5rErvwUF2JSnrrfWKPQRkdzwi418WPTv",  # noqa
            "0225bf6018b3ddf3fb0158aa0b450c256f8218e2dd1ac002c29c5bb836a8550918"  # noqa
        ),
        "m/44'/0'/1'/1/1": (
            "16SCgCy1p6FGU9ER4AEBo7QYiDPw7RwVRG",  # noqa
            "02701cefb54958340a21e3389359bfba70c1a5dfefcdd0703692a0a5ba76d61131"  # noqa
        ),
        "m/44'/0'/1'/1/2": (
            "1GrEuCC3qHE3DexW1Bq71qkagB8w9HkVJq",  # noqa
            "0358152e62878dc3e0d3ce53abc2fa18d0035ec3ef51ddb84e67661d44e9ff7219"  # noqa
        ),
        "m/44'/0'/1'/1/3": (
            "1FmbdJzwC5z47Y3ax4dQR5AnH8ssGjXpiE",  # noqa
            "02616274975cef0d5858fb4eda4b9db1287255b3c12c5d922cce31d1f04fe00300"  # noqa
        ),
        "m/44'/0'/1'/1/4": (
            "1DtbYzZSbq8TYmrUbF2sci1etD3unPqAk7",  # noqa
            "02a123755a3df913667ee82847a523ca678a6720e33d16554852b32d22b005629e"  # noqa
        ),
        "m/44'/0'/1'/1/5": (
            "1JJUmoG9ZHHHQoA8pW9VRfhQfA3Z4HCNzQ",  # noqa
            "02deb663dc194d54ded17cdbf039d517785f061c53bdf997328747aa17f50f92d1"  # noqa
        ),
    },
)


class TestHdAddressIterator(TestCaseApplication):
    def test_hd_list(self) -> None:
        for hd_list in HD_ADDRESS_LIST:
            count = 0
            root_node = HdNode.deriveRootNode(bytes.fromhex(hd_list["seed"]))
            self.assertIsNotNone(root_node)

            coin = Bitcoin(model_factory=self._application.modelFactory)
            self.assertTrue(coin.deriveHdNode(root_node))

            it = HdAddressIterator(coin)
            for address in it:
                it.markCurrentAddress(True)
                path = address.key.pathToString(hardened_char="'")
                if path in hd_list:
                    count += 1
                    self.assertEqual(
                        hd_list[path][0],
                        address.name)
                    self.assertEqual(
                        hd_list[path][1],
                        address.publicKey.data.hex())
                    key = coin.Address.importKey(coin, path)
                    self.assertIsNotNone(key)
                    self.assertEqual(
                        hd_list[path][1],
                        key.publicKey.data.hex())
            self.assertEqual(48, count)

    def test(self) -> None:
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)

        coin = Bitcoin(model_factory=self._application.modelFactory)
        self.assertTrue(coin.deriveHdNode(root_node))

        flush = 0
        append = 0
        while flush < 1 or append < 1:
            it = HdAddressIterator(coin)
            flush = 0
            append = 0

            for _ in it:
                if not 0 < randint(0, 10) <= 3:
                    flush += 1
                    it.markCurrentAddress(True)
                    # noinspection PyProtectedMember
                    self.assertLess(0, it._empty_address_count)
                else:
                    append += 1
                    it.markCurrentAddress(False)
                    # noinspection PyProtectedMember
                    self.assertEqual(0, it._empty_address_count)
