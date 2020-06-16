
import unittest
import random
import pathlib
from client.wallet import serialization


class Test_base(unittest.TestCase):
    PSW = "()90()OP()!@op"
    FPATH = "test._dat"

    @classmethod
    def tearDownClass(cls):
        fl = pathlib.Path(cls.FPATH)
        if fl.exists():
            fl.unlink()


    def test_encryption(self):
        ser = serialization.Serializator(
            serialization.SerializationType.CYPHER | serialization.SerializationType.DEBUG, self.PSW)

        def any_list(len_):
            for i in range(0, len_):
                yield str(f"{i**3}"*i) if i % 3 == 0 else i**2
        table = {
            "key_dict": {
                "sub_int": random.randint(1, 1e4),
                "sub_real": random.random(),
            },
            "key_list": list(any_list(10)),
            "plain": random.randint(1, 1e3),
        }
        for k, v in table.items():
            ser.add_one(k, v)
        ser.to_file(self.FPATH)
        ##
        deser = serialization.DeSerializator(self.FPATH, self.PSW)
        for k, v in table.items():
            self.assertEqual(table[k], deser[k])
