

import unittest
import logging
from bmnclient import orderedset
log = logging.getLogger(__name__)


class TestOrderSet(unittest.TestCase):

    def test_insert(self):
        oset = orderedset.OrderedSet(range(20))
        self.assertEqual(oset.index(4), 4)
        self.assertEqual(oset.index(5), 5)
        oset.add(100, 5)
        self.assertEqual(oset.index(100), 6)
        self.assertEqual(oset.index(4), 4)
        self.assertEqual(oset.index(5), 6)
        oset.raw_add(101)
        self.assertEqual(oset.index(101), 21)
        oset.add(102, 7)
        self.assertEqual(oset.index(5), 6)
        oset.add(103, 6)
        self.assertEqual(oset.index(5), 7)
        self.assertEqual(oset.add(200), oset.add(200))
        self.assertEqual(oset.raw_add(201), oset.raw_add(201))

    def test_insert_many(self):
        oset = orderedset.OrderedSet(range(20))
        oset.extend(range(30, 35))
        self.assertEqual(oset.index(30), 20)
        self.assertEqual(oset.index(34), 24)
        oset.extend(range(40, 45) , 10)
        self.assertEqual(oset.index(40), 10)
        self.assertEqual(oset.index(44), 14)

    def test_remove(self):
        oset = orderedset.OrderedSet(range(20))
        oset.remove(5, 10)
        olist = list(oset)
        self.assertEqual(list(range(5)), olist[:5])
        self.assertEqual(list(range(15, 20)), olist[-5:])
        self.assertEqual(oset.index(3), 3)
        self.assertEqual(oset.index(18), 8)

        oset.remove(0, 4)
        olist = list(oset)
        self.assertEqual(list(range(15, 20)), olist[1:])
        self.assertEqual(oset.index(18), 4)

        with self.assertRaises(IndexError):
            oset.remove(10)

        oset.remove(0, 100)

        self.assertFalse(oset)
