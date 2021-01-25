from unittest import TestCase

from bmnclient import version
from bmnclient.crypto.base58 import Base58

TEST_LIST = (
    (
        "3QJmnh",
        "5df6e0e2"
    ), (
        "11",
        "0000"
    ), (
        "",
        ""
    ), (
        "2NEpo7TZRhna7vSvL",
        "Hello world!".encode(encoding=version.ENCODING).hex()
    ), (
        "BAD_",
        None
    ),
)

TEST_LIST_CHECK = (
    (
        "16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",
        "00010966776006953d5567439e5e39f86a0d273beed61967f6"
    ), (
        "3Ps86GT6vHg7dCT5QhcECDFkRaUJbBzqXB",
        "05f33c134a48d70818bdc2cf09631316ce90f713662ecee51e"
    ), (
        "1PMycacnJaSqwwJqjawXBErnLsZ7RkXUAs",
        "00f54a5851e9372b87810a8e60cdd2e7cfd80b6e31c7f18fe8"
    ), (
        "1axVFjCkMWDFCHjQHf99AsszXTuzxLxxg",
        "00066c0b8995c7464e89f6760900ea6978df18157388421561"
    ), (
        "1axVFjCkMWDFCHjQHf99AsszXTuzxLxxG",
        None
    ),
)


class TestBase58(TestCase):
    def test_encode(self) -> None:
        for (address, value) in TEST_LIST:
            if not value:
                continue
            value = bytes.fromhex(value)
            result = Base58.encode(value, False)
            self.assertEqual(address, result)

        for (address, value) in TEST_LIST_CHECK:
            if not value:
                continue
            value = bytes.fromhex(value)[:-4]
            result = Base58.encode(value, True)
            self.assertEqual(address, result)

    def test_decode(self) -> None:
        for (address, value) in TEST_LIST:
            value = bytes.fromhex(value) if value is not None else None
            result = Base58.decode(address, False)
            self.assertEqual(value, result)

        for (address, value) in TEST_LIST_CHECK:
            value = bytes.fromhex(value)[:-4] if value is not None else None
            result = Base58.decode(address, True)
            if not value:
                self.assertEqual(None, result)
            else:
                self.assertEqual(value, result)
