from unittest import TestCase

from bmnclient.utils import (
    DeserializeFlag,
    Serializable,
    SerializeFlag,
    serializable)


class A(Serializable):
    def __init__(
            self,
            *,
            value1_a: int = 1,
            value2_b: int = 2,
            value3_c: int = 2) -> None:
        super().__init__()
        self._v1 = value1_a
        self._v2 = value2_b
        self._v3 = value3_c

    @serializable
    @property
    def value1A(self) -> int:
        return self._v1

    @value1A.setter
    def value1A(self, v: int) -> None:
        self._v1 = v

    @serializable
    @property
    def value2B(self) -> int:
        return self._v2

    @serializable(data3=123)
    @property
    def value3C(self) -> int:
        return self._v3


class B(A):
    def __update__(self, **kwargs) -> bool:
        return super().__update__(**kwargs)


class TestSerializable(TestCase):
    def test_basic(self) -> None:
        for s_flag in SerializeFlag:
            a1 = A()
            self.assertEqual(3, len(a1.serializeMap))
            self.assertEqual(3, len(a1.serialize(s_flag)))
            self.assertEqual(a1.value1A, a1.serialize(s_flag)["value1_a"])
            self.assertEqual(a1.value2B, a1.serialize(s_flag)["value2_b"])
            self.assertEqual(a1.value3C, a1.serialize(s_flag)["value3_c"])

            for d_flag in DeserializeFlag:
                a2 = A.deserialize(d_flag, a1.serialize(s_flag))
                self.assertEqual(a1.value1A, a2.value1A)
                self.assertEqual(a1.value2B, a2.value2B)
                self.assertEqual(a1.value3C, a2.value3C)
                self.assertEqual(a1.serialize(s_flag), a2.serialize(s_flag))

            self.assertEqual(1, len(a1.serializeMap["value1_a"]))
            self.assertEqual("value1A", a1.serializeMap["value1_a"]["name"])

            self.assertEqual(1, len(a1.serializeMap["value2_b"]))
            self.assertEqual("value2B", a1.serializeMap["value2_b"]["name"])

            self.assertEqual(2, len(a1.serializeMap["value3_c"]))
            self.assertEqual("value3C", a1.serializeMap["value3_c"]["name"])
            self.assertEqual(123, a1.serializeMap["value3_c"]["data3"])

    def test_source(self) -> None:
        for s_flag in SerializeFlag:
            source = {
                "value1_a": 101,
                "value2_b": 202,
                "value3_c": 303
            }

            a1 = A(**source)
            self.assertEqual(a1.value1A, source["value1_a"])
            self.assertEqual(a1.value2B, source["value2_b"])
            self.assertEqual(a1.value3C, source["value3_c"])
            self.assertEqual(a1.value1A, a1.serialize(s_flag)["value1_a"])
            self.assertEqual(a1.value2B, a1.serialize(s_flag)["value2_b"])
            self.assertEqual(a1.value3C, a1.serialize(s_flag)["value3_c"])

            a2 = A()
            self.assertNotEqual(a2.value1A, source["value1_a"])
            self.assertNotEqual(a2.value2B, source["value2_b"])
            self.assertNotEqual(a2.value3C, source["value3_c"])

            for d_flag in DeserializeFlag:
                self.assertRaises(
                    KeyError,
                    a2.deserializeUpdate,
                    d_flag,
                    {"value_three": 303})
                self.assertRaises(
                    ValueError,
                    a2.deserializeUpdate,
                    d_flag,
                    source)
                self.assertEqual(a2.value1A, source["value1_a"])
                self.assertEqual(a2.value2B, A().value2B)

                self.assertTrue(a2.deserializeUpdate(
                    d_flag,
                    {"value1_a": 1001}))
                self.assertEqual(a2.value1A, 1001)
                self.assertEqual(a2.value2B, A().value2B)

                b1 = B(**source)
                self.assertEqual(a1.serialize(s_flag), b1.serialize(s_flag))
                b1.deserializeUpdate(
                    d_flag,
                    {"value1_a": 10001})
                self.assertEqual(b1.value1A, 10001)
                self.assertEqual(b1.value2B, a1.value2B)
