

import unittest
import logging
from client import orderedset
log = logging.getLogger(__name__)


class TestOrderSet(unittest.TestCase):

    def test_remove(self):
        oset = orderedset.OrderedSet(range(20))

        oset.remove(5, 10)
        olist = list(oset)
        self.assertEqual(list(range(5)), olist[:5])
        self.assertEqual(list(range(15, 20)), olist[-5:])
        self.assertEqual(oset.index(3),3)
        self.assertEqual(oset.index(18),8)

        oset.remove(0, 4)
        olist = list(oset)
        self.assertEqual(list(range(15,20)), olist[1:])
        self.assertEqual(oset.index(18),4)

        with self.assertRaises(IndexError):
            oset.remove(10)

        oset.remove(0,100)

        self.assertFalse(oset)