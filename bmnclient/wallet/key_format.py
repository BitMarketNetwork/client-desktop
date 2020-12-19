
import logging
from . import util
log = logging.getLogger(__name__)


class KeyFormatError(Exception):
    pass

class KeyFormat:
    name = None
    length = None

    @classmethod
    def recognize(cls, key):
        if isinstance(key,(tuple,list)):
            return KeyFormatDec
        pkfs =  ( val for _ , val in globals().items() if isinstance(val,type) and issubclass(val,cls) )
        for pkf in pkfs:
            if len(key) == pkf.length and cls.test(key):
                return pkf
        raise KeyFormatError("Public key isn't recognized")

    @classmethod
    def test(cls, key):
        return True

    @classmethod
    def encode(cls,pub):
        raise KeyFormatError("Invalid key format")

    @classmethod
    def decode(cls,pub):
        raise KeyFormatError("Invalid key format")
        

class KeyFormatDec(KeyFormat):
    name = "decimal"

    @classmethod
    def encode(pub):
        return pub

class KeyFormatBin(KeyFormat):
    name = "bin"
    length = 65

    @classmethod
    def encode(cls, key):
        return b'\x04' + key.CKey_256.encode(pub[0],32) + key.CKey_256.encode(pub[1],32) 

    @classmethod
    def test(cls, key):
        return key[0] == 4

class KeyFormatHex(KeyFormat):
    name = "hex"
    length = 130

    @classmethod
    def test(cls, key):
        return key[:2] == "04"

class KeyFormatBinCompressed(KeyFormat):
    name = "bin_compressed"
    length = 33

    @classmethod
    def test(cls, key):
        return key[0] in [2,3]

class KeyFormatHexCompressed(KeyFormat):
    name = "hex_compressed"
    length = 66

    @classmethod
    def test(cls, key):
        return key[:2] in ['02', '03']

class KeyFormatBinElectrum(KeyFormat):
    name = "bin_electrum"
    length = 64


class KeyFormatHexElectrum(KeyFormat):
    name = "hex_electrum"
    length = 128