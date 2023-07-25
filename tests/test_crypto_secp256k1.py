from __future__ import annotations

from unittest import TestCase

from bmnclient.crypto.base58 import Base58
from bmnclient.crypto.bech32 import Bech32
from bmnclient.crypto.digest import Hash160Digest
from bmnclient.crypto.secp256k1 import KeyUtils, PrivateKey

# https://learnmeabitcoin.com/technical/wif
# https://learnmeabitcoin.com/technical/public-key
# https://kimbatt.github.io/btc-address-generator
KEY_LIST = (
    {
        "compressed": False,
        "version": 0x80,
        "wif": "5JJn4Wrgto5sMzwjNQTffLcuK1eFBGYCoDWCRNyLAY2v6HN79eC",  # noqa
        "private_key": "40b13f860f16e0e206a0aa42357d8f4f415f18871c064991b5d72bbfc70c428d",  # noqa
        "public_key": "047c33ae13a6ced62cc56d8c6914286442c3d7708572c79b5225a978338d2f08b6db753cc1d69164a4acbf14031fcdbc2bc22b55554e8bc7ce8b29f2d2b3e4dc63",  # noqa
        "base58_address": "1MnKUrE8z45ytHWFEeLSTSgSEnCWDLaELd",  # noqa
        "bech32_address": None,
    },
    {
        "compressed": True,
        "version": 0x80,
        "wif": "KzSpUWDRDULN2xEMR1q5sM5ajo8Xuxi9ooDV58w2wif3nm45SAMR",  # noqa
        "private_key": "604173fc85df6d1c50140ca31eac25c76d9ebfb9a1055e9ec317889f135d5d39",  # noqa
        "public_key": "037d9078ad1bf968b6612b21db4c9bd54bfb31d5b4214f9ecc1da25bfc487fae64",  # noqa
        "base58_address": "1CpPydKVzKqfuX78CXdc7vhzx9Xv4SQ2CN",  # noqa
        "bech32_address": "bc1qsxsp6rt3grkans2wgu5ldmjjml87s2qjsszmt5",  # noqa
    },
    {
        "compressed": True,
        "version": 0x80,
        "wif": "Kz6UJmQACJmLtaQj5A3JAge4kVTNQ8gbvXuwbmCj7bsaabudb3RD",  # noqa
        "private_key": "55c9bccb9ed68446d1b75273bbce89d7fe013a8acd1625514420fb2aca1a21c4",  # noqa
        "public_key": "02157bc6dc9dc7a25d537f36d4714c0cfc11c882f017a989e16956cc1aa8cce20a",  # noqa
        "base58_address": "12Vox8pNW85dFotFrpdAWBM9KN6TuCtX4m",  # noqa
        "bech32_address": "bc1qzp40wyx4hxjty05pzdrfmk5uwzydvrl3twcqtk",  # noqa
    },
    {
        "compressed": False,
        "version": 0x80,
        "wif": "5KHxtARu5yr1JECrYGEA2YpCPdh1i9ciEgQayAF8kcqApkGzT9s",  # noqa
        "private_key": "c28a9f80738f770d527803a566cf6fc3edf6cea586c4fc4a5223a5ad797e1ac3",  # noqa
        "public_key": "043d5c2875c9bd116875a71a5db64cffcb13396b163d039b1d932782489180433476a4352a2add00ebb0d5c94c515b72eb10f1fd8f3f03b42f4a2b255bfc9aa9e3",  # noqa
        "base58_address": "1ELReFsTCUY2mfaDTy32qxYiT49z786eFg",  # noqa
        "bech32_address": None,
    },
)


class TestSecp256k1(TestCase):
    def test_key_list(self) -> None:
        for key_data in KEY_LIST:
            (version, key) = PrivateKey.fromWif(key_data["wif"])
            self.assertIsNotNone(key)
            self.assertEqual(key_data["compressed"], key.isCompressed)
            self.assertEqual(key_data["version"], version)
            self.assertEqual(key_data["private_key"], key.data.hex())

            self.assertEqual(key_data["public_key"], key.publicKey.data.hex())

            self.assertEqual(key_data["wif"], key.toWif(key_data["version"]))
            self.assertNotEqual(
                key_data["wif"], key.toWif(key_data["version"] + 1)
            )

            signature1 = key.sign(b"Hello1")
            self.assertIsNotNone(signature1)
            self.assertGreater(len(signature1), 1)
            self.assertTrue(key.publicKey.verify(signature1, b"Hello1"))
            self.assertFalse(key.publicKey.verify(signature1, b"Hello2"))

            b = Base58.decode(key_data["base58_address"])
            self.assertIsNotNone(b)
            b_version = KeyUtils.integerToBytes(b[0], 1)
            self.assertIsNotNone(b_version)
            b = Base58.encode(
                b_version + Hash160Digest(key.publicKey.data).finalize()
            )
            self.assertEqual(key_data["base58_address"], b)

            if key_data["bech32_address"] is None:
                self.assertFalse(key.isCompressed)
            else:
                (b_hrp, b_version, _) = Bech32.decode(
                    key_data["bech32_address"]
                )
                self.assertIsNotNone(b_hrp)
                self.assertIsNotNone(b_version)
                b = Bech32.encode(
                    b_hrp,
                    b_version,
                    Hash160Digest(key.publicKey.data).finalize(),
                )
                self.assertEqual(key_data["bech32_address"], b)
