
class AddressBase:
    pass


class CoinBase:
    @property
    def shortName(self) -> str:
        raise NotImplementedError

    @property
    def fullName(self) -> str:
        raise NotImplementedError

    def stringToAmount(self, source: str) -> int:
        raise NotImplementedError

    def amountToString(self, amount: int) -> str:
        raise NotImplementedError

    def decodeAddress(self, source: str) -> AddressBase:
        raise NotImplementedError

    def encodeAddress(self, address: AddressBase) -> AddressBase:
        raise NotImplementedError


class Bitcoin(CoinBase):
    @property
    def shortName(self) -> str:
        return "btc"

    @property
    def fullName(self) -> str:
        return "Bitcoin"

    def stringToAmount(self, source: str) -> int:
        raise NotImplementedError

    def amountToString(self, amount: int) -> str:
        raise NotImplementedError

    def decodeAddress(self, source: str) -> AddressBase:
        raise NotImplementedError

    def encodeAddress(self, address: AddressBase) -> AddressBase:
        raise NotImplementedError


class BitcoinTest(Bitcoin):
    @property
    def shortName(self) -> str:
        return "btctest"

    @property
    def fullName(self) -> str:
        return "Bitcoin Testnet"


class Litecoin(Bitcoin):
    @property
    def shortName(self) -> str:
        return "ltc"

    @property
    def fullName(self) -> str:
        return "Litecoin"
