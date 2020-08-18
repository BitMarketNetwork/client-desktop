

import unittest
from client.wallet import util


class TestBip38(unittest.TestCase):

    def setUp(self):
        self.BIP_CASES_1 = [
            {
                "title": "No compression, no EC multiply",
                "passphrase": "TestingOneTwoThree",
                "encrypted": "6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg",
                "WIF": "5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR",
                "hex": "CBF4B9F70470856BB4F40F80B87EDB90865997FFEE6DF315AB166D713AF433A5",
            },
            {
                "title": "No compression, no EC multiply",
                "passphrase": "Satoshi",
                "encrypted": "6PRNFFkZc2NZ6dJqFfhRoFNMR9Lnyj7dYGrzdgXXVMXcxoKTePPX1dWByq",
                "WIF": "5HtasZ6ofTHP6HCwTqTkLDuLQisYPah7aUnSKfC7h4hMUVw2gi5",
                "hex": "09C2686880095B1A4C249EE3AC4EEA8A014F11E6F986D0B5025AC1F39AFBD9AE",
            },
            {
                "title": "No compression, no EC multiply",
                "passphrase": """ϓ␀𐐀💩 (<tt>\u03D2\u0301\u0000\U00010400\U0001F4A9</tt>; [http://codepoints.net/U+03D2 GREEK UPSILON WITH \
                    HOOK], [http://codepoints.net/U+0301 COMBINING ACUTE ACCENT], [http://codepoints.net/U+0000 NULL],\
                         [http://codepoints.net/U+10400 DESERET CAPITAL LETTER LONG I], [http://codepoints.net/U+1F4A9 PILE OF POO])""",
                "encrypted": "6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg",
                "WIF": "5Jajm8eQ22H3pGWLEVCXyvND8dQZhiQhoLJNKjYXk9roUFTMSZ4",
                "btc": "16ktGzmfrurhbhi6JGqsMWf7TyqK9HNAeF",
                "note": "The non-standard UTF-8 characters in this passphrase should be NFC normalized to \
                    result in a passphrase of 0xcf9300f0909080f09f92a9 before further processing",
            },
        ]
        self.BIP_CASES_2 = [
            {
                "title": "Compression, no EC multiply",
                "passphrase": "TestingOneTwoThree",
                "encrypted": "6PYNKZ1EAgYgmQfmNVamxyXVWHzK5s6DGhwP4J5o44cvXdoY7sRzhtpUeo",
                "WIF": "L44B5gGEpqEDRS9vVPz7QT35jcBG2r3CZwSwQ4fCewXAhAhqGVpP",
                "hex": "CBF4B9F70470856BB4F40F80B87EDB90865997FFEE6DF315AB166D713AF433A5",
            },
            {
                "title": "Compression, no EC multiply",
                "passphrase": "Satoshi",
                "encrypted": "6PYLtMnXvfG3oJde97zRyLYFZCYizPU5T3LwgdYJz1fRhh16bU7u6PPmY7",
                "WIF": "KwYgW8gcxj1JWJXhPSu4Fqwzfhp5Yfi42mdYmMa4XqK7NJxXUSK7",
                "hex": "09C2686880095B1A4C249EE3AC4EEA8A014F11E6F986D0B5025AC1F39AFBD9AE",
            },
        ]
        self.BIP_CASES_3 = [
            {
                "title": "EC multiply, no compression, no lot/sequence numbers",
                "passphrase": "TestingOneTwoThree",
                "passcode": "passphrasepxFy57B9v8HtUsszJYKReoNDV6VHjUSGt8EVJmux9n1J3Ltf1gRxyDGXqnf9qm",
                "encrypted": "6PfQu77ygVyJLZjfvMLyhLMQbYnu5uguoJJ4kMCLqWwPEdfpwANVS76gTX",
                "btc": "1PE6TQi6HTVNz5DLwB1LcpMBALubfuN2z2",
                "WIF": "5K4caxezwjGCGfnoPTZ8tMcJBLB7Jvyjv4xxeacadhq8nLisLR2",
                "hex": "A43A940577F4E97F5C4D39EB14FF083A98187C64EA7C99EF7CE460833959A519",
            },
            {
                "title": "EC multiply, no compression, no lot/sequence numbers",
                "passphrase": "Satoshi",
                "passcode": "passphraseoRDGAXTWzbp72eVbtUDdn1rwpgPUGjNZEc6CGBo8i5EC1FPW8wcnLdq4ThKzAS",
                "encrypted": "6PfLGnQs6VZnrNpmVKfjotbnQuaJK4KZoPFrAjx1JMJUa1Ft8gnf5WxfKd",
                "btc": "1CqzrtZC6mXSAhoxtFwVjz8LtwLJjDYU3V",
                "WIF": "5KJ51SgxWaAYR13zd9ReMhJpwrcX47xTJh2D3fGPG9CM8vkv5sH",
                "hex": "C2C8036DF268F498099350718C4A3EF3984D2BE84618C2650F5171DCC5EB660A",
            },
        ]
        self.BIP_CASES_4 = [
            {
                "title": "EC multiply, no compression, lot/sequence numbers",
                "passphrase": "MOLON LABE",
                "passcode": "passphraseaB8feaLQDENqCgr4gKZpmf4VoaT6qdjJNJiv7fsKvjqavcJxvuR1hy25aTu5sX",
                "encrypted": "6PgNBNNzDkKdhkT6uJntUXwwzQV8Rr2tZcbkDcuC9DZRsS6AtHts4Ypo1j",
                "btc": "1Jscj8ALrYu2y9TD8NrpvDBugPedmbj4Yh",
                "WIF": "5JLdxTtcTHcfYcmJsNVy1v2PMDx432JPoYcBTVVRHpPaxUrdtf8",
                "hex": "44EA95AFBF138356A05EA32110DFD627232D0F2991AD221187BE356F19FA8190",
                "confirm": "cfrm38V8aXBn7JWA1ESmFMUn6erxeBGZGAxJPY4e36S9QWkzZKtaVqLNMgnifETYw7BPwWC9aPD",
                "lot": "263183/1",
            },
            {
                "title": "EC multiply, no compression, lot/sequence numbers",
                "passphrase": "ΜΟΛΩΝ ΛΑΒΕ",
                "passcode": "passphrased3z9rQJHSyBkNBwTRPkUGNVEVrUAcfAXDyRU1V28ie6hNFbqDwbFBvsTK7yWVK",
                "encrypted": "6PgGWtx25kUg8QWvwuJAgorN6k9FbE25rv5dMRwu5SKMnfpfVe5mar2ngH",
                "btc": "1Lurmih3KruL4xDB5FmHof38yawNtP9oGf",
                "WIF": "5KMKKuUmAkiNbA3DazMQiLfDq47qs8MAEThm4yL8R2PhV1ov33D",
                "hex": "CA2759AA4ADB0F96C414F36ABEB8DB59342985BE9FA50FAAC228C8E7D90E3006",
                "confirm": "cfrm38V8G4qq2ywYEFfWLD5Cc6msj9UwsG2Mj4Z6QdGJAFQpdatZLavkgRd1i4iBMdRngDqDs51",
                "lot": "806938/1",
            },
        ]

    def _test_case(self, **kwargs):
        print(f"case: {kwargs.pop('title')}")

    def _test_cases(self, cases):
        [self._test_case(**case) for case in cases]

    def test_1(self):
        self._test_cases(self.BIP_CASES_1)

    def test_2(self):
        self._test_cases(self.BIP_CASES_2)

    def test_3(self):
        self._test_cases(self.BIP_CASES_3)

    def test_4(self):
        self._test_cases(self.BIP_CASES_4)
