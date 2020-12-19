
import unittest
import hmac
import hashlib
from bmnclient.wallet import util
from bmnclient.wallet import coin_network
from bmnclient.wallet import hd


class TestBip32(unittest.TestCase):

    def setUp(self):
        self.BIP_CASE_1 = {
            "title": "bip32 case 1",
            "seed": "000102030405060708090a0b0c0d0e0f",
            "m": ("xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8",
                  "xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi"),
            "m/0H": ("xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw",
                     "xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7"
                     ),
            "m/0H/1": ("xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ",
                       "xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs"
                       ),
            "m/0H/1/2H": ("xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5",
                          "xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM"
                          ),
            "m/0H/1/2H/2": ("xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV",
                            "xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334"
                            ),
            "m/0H/1/2H/2/1000000000": ("xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy",
                                       "xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76"
                                       ),
        }
        self.BIP_CASE_2 = {
            "title": "bip32 case 2",
            "seed": "fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542",
            "m": ("xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB",
                  "xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U"),
            "m/0": ("xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH",
                    "xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt"),
            "m/0/2147483647H": ("xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a",
                                "xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9"),
            "m/0/2147483647H/1": ("xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon",
                                  "xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef"),
            "m/0/2147483647H/1/2147483646H": ("xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL",
                                              "xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc"),
            "m/0/2147483647H/1/2147483646H/2": ("xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt",
                                                "xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j"),
        }
        self.BIP_CASE_3 = {
            "title": "bip32 case 3",
            "seed": "4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be",
            "m": ("xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13",
                  "xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6"),
            "m/0H": ("xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y",
                     "xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L"),
        }

    def _export(self, pkey, chain, priv: bool, depth: int = 0, fingerprint=0, child: int = 0) -> str:
        c256 = util.CKey_256
        res = c256.encode(
            coin_network.BitcoinMainNetwork.EX_PREFIX_PRV if priv else coin_network.BitcoinMainNetwork.EX_PREFIX_PUB, 4)  # version bytes
        res += c256.encode(depth, 1)  # depth
        if isinstance(fingerprint, int):
            res += c256.encode(fingerprint, 4)  # fingerprint
        else:
            res += fingerprint
        res += c256.encode(child, 4)  # child number
        res += chain
        if priv:
            pkey = b'\00' + pkey
        self.assertEqual(33, len(pkey))
        res += pkey
        self.assertEqual(78, len(res))
        return util.b58_check_encode(res)

    def _test_hd_raw(self, **kwargs):
        """
        let's leave this test
        """
        raise NotImplementedError("no more pybmn module")
        hex_seed = bytes.fromhex(kwargs["seed"])
        I = hmac.new(b"Bitcoin seed", hex_seed, hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]
        ec = pybmn.ECKey()
        ec.set_secret(Il)
        ec.compressed = True
        self.assertTrue(ec.is_valid)
        pub = ec.get_public_key()
        self.assertEqual(33, len(pub))
        # public master
        check_58 = self._export(pub, Ir, False)
        self.assertEqual(check_58, kwargs["m"][0])
        # private master
        priv = ec.get_private_key()
        check_58 = self._export(priv, Ir, True)
        self.assertEqual(check_58, kwargs["m"][1])
        master_fp = util.hash160(pub)[:4]
        master_chain = Ir
        # first children
        h0 = "m/0H" in kwargs
        N = hd.SECP256k1_N
        # first private
        index = 0
        if h0:
            index = hd.HDNode.make_hardened_index(index)
            I = hmac.new(master_chain, b'\00' + priv + index.to_bytes(length=4,
                                                                      byteorder="big"), hashlib.sha512).digest()
        else:
            I = hmac.new(master_chain, pub + index.to_bytes(length=4,
                                                            byteorder="big"), hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]
        p256_Il = int.from_bytes(Il, byteorder="big")
        p256_Il += int.from_bytes(priv, byteorder="big") % N
        p256_Il %= N
        child = index
        child_prv = p256_Il.to_bytes(32, byteorder="big")
        check_58_prv = self._export(
            child_prv, Ir, True, 1, fingerprint=master_fp, child=child)
        ep = pybmn.ECPoint(pub)
        ep.g_mul(Il)
        child_pub = ep.content
        check_58_pub = self._export(
            child_pub, Ir, False, 1, fingerprint=master_fp, child=child)
        child_chain = Ir
        ##
        if h0:
            self.assertEqual(check_58_prv, kwargs["m/0H"][1])
            self.assertEqual(check_58_pub, kwargs["m/0H"][0])
        else:
            self.assertEqual(check_58_prv, kwargs["m/0"][1])
            self.assertEqual(check_58_pub, kwargs["m/0"][0])
        # eckey check
        eck = pybmn.ECKey(child_prv)
        self.assertEqual(child_prv, eck.get_private_key())
        self.assertEqual(child_pub, eck.get_public_key())
        # try third level
        THIRD = "m/0H/1"
        if h0 and THIRD in kwargs:
            index = 1
            I = hmac.new(child_chain, child_pub + index.to_bytes(length=4,
                                                                 byteorder="big"), hashlib.sha512).digest()
            Il, Ir = I[:32], I[32:]
            p256_Il = int.from_bytes(Il, byteorder="big")
            p256_Il += int.from_bytes(child_prv, byteorder="big") % N
            p256_Il %= N
            child_prv = p256_Il.to_bytes(32, byteorder="big")
            fp = util.hash160(child_pub)[:4]
            check_58_prv = self._export(
                child_prv, Ir, True, 2, fingerprint=fp, child=index)
            self.assertEqual(check_58_prv, kwargs[THIRD][1], THIRD)
            ep = pybmn.ECPoint(child_pub)
            ep.g_mul(Il)
            child_pub = ep.content
            check_58_pub = self._export(
                child_pub, Ir, False, 2, fingerprint=fp, child=index)
            self.assertEqual(check_58_pub, kwargs[THIRD][0], THIRD)

    def _test_hd_high(self, **kwargs):
        hex_seed = bytes.fromhex(kwargs.pop("seed"))
        title = kwargs.pop("title")
        master = hd.HDNode.make_master(
            hex_seed, coin_network.BitcoinMainNetwork)
        self.assertEqual(master.extended_key, kwargs["m"][1], "master prv")
        self.assertEqual(master.public_hd_key.extended_key,
                         kwargs["m"][0], "master pub")
        for name, (pub, prv) in kwargs.items():
            print(f"check name {name} from {title}")
            key = master.from_chain_path(name)
            self.assertEqual(key.key.public_key.compressed_bytes,
                             key.public_hd_key.key.compressed_bytes)
            self.assertEqual(key.public_hd_key.extended_key, pub, name)
            self.assertEqual(key.extended_key, prv, name)
            self.assertEqual(key.chain_path, name)
            parsed_key = hd.HDNode.from_extended_key(key.extended_key, None)
            self.assertEqual(key, parsed_key)
            # test generation from child
            if name.count("/") > 1:
                child_name = "/".join(name.split("/")[:3])
                child = master.from_chain_path(child_name)
                grand = child.from_chain_path(name)
                self.assertEqual(grand, key)
                parsed_child = hd.HDNode.from_extended_key(
                    child.extended_key, None)
                self.assertEqual(child, parsed_child)

    def test_hd(self):
        # self._test_hd_raw(**self.BIP_CASE_1)
        self._test_hd_high(**self.BIP_CASE_1)
        # self._test_hd_raw(**self.BIP_CASE_2)
        self._test_hd_high(**self.BIP_CASE_2)
        # self._test_hd_raw(**self.BIP_CASE_3)
        self._test_hd_high(**self.BIP_CASE_3)
