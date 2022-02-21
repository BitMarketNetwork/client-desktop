from unittest import TestCase

from bmnclient.utils.serialize import Serializable, serializable


class A(Serializable):
    def __init__(self, *, value_one: int = 1, value_two: int = 2) -> None:
        super().__init__()
        self._v1 = value_one
        self._v2 = value_two

    @serializable
    @property
    def valueOne(self) -> int:
        return self._v1

    @valueOne.setter
    def valueOne(self, v: int) -> None:
        self._v1 = v

    @serializable
    @property
    def valueTwo(self) -> int:
        return self._v2


class B(A):
    def __update__(self, *args, **kwargs) -> bool:
        return super().__update__(*args, **kwargs)


class TestSerializable(TestCase):
    def test_basic(self) -> None:
        a1 = A()
        self.assertEqual(2, len(a1.serializeMap))
        self.assertEqual(2, len(a1.serialize()))
        self.assertEqual(a1.valueOne, a1.serialize()["value_one"])
        self.assertEqual(a1.valueTwo, a1.serialize()["value_two"])

        a2 = A.deserialize(a1.serialize())
        self.assertEqual(a1.valueOne, a2.valueOne)
        self.assertEqual(a1.valueTwo, a2.valueTwo)
        self.assertEqual(a1.serialize(), a2.serialize())

    def test_source(self) -> None:
        source = {
            "value_one": 101,
            "value_two": 202
        }

        a1 = A(**source)
        self.assertEqual(a1.valueOne, source["value_one"])
        self.assertEqual(a1.valueTwo, source["value_two"])
        self.assertEqual(a1.valueOne, a1.serialize()["value_one"])
        self.assertEqual(a1.valueTwo, a1.serialize()["value_two"])

        a2 = A()
        self.assertNotEqual(a2.valueOne, source["value_one"])
        self.assertNotEqual(a2.valueTwo, source["value_two"])

        self.assertRaises(
            KeyError,
            a2.deserializeUpdate,
            {"value_three": 303})
        self.assertRaises(
            ValueError,
            a2.deserializeUpdate,
            source)
        self.assertEqual(a2.valueOne, source["value_one"])
        self.assertEqual(a2.valueTwo, A().valueTwo)

        self.assertTrue(a2.deserializeUpdate({"value_one": 1001}))
        self.assertEqual(a2.valueOne, 1001)
        self.assertEqual(a2.valueTwo, A().valueTwo)

        b1 = B(**source)
        self.assertEqual(a1.serialize(), b1.serialize())
        b1.deserializeUpdate({"value_one": 10001})
        self.assertEqual(b1.valueOne, 10001)
        self.assertEqual(b1.valueTwo, a1.valueTwo)
