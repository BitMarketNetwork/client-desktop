class CoinNetworkBase:
    pass


class BitcoinMainNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x00'
    SCRIPT_BYTE_PREFIX = b'\x05'


class BitcoinTestNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x6f'
    SCRIPT_BYTE_PREFIX = b'\xc4'


class LitecoinMainNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x30'
    SCRIPT_BYTE_PREFIX = b'\x05'
    SCRIPT_BYTE_PREFIX_2 = b'\x32'


class LitecoinTestNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x6f'
    SCRIPT_BYTE_PREFIX = b'\xc4'
    SCRIPT_BYTE_PREFIX_2 = b'\x3A'


PUBLIC_HASH_LIST = [
    BitcoinMainNetwork.ADDRESS_BYTE_PREFIX,
    BitcoinTestNetwork.ADDRESS_BYTE_PREFIX,
    LitecoinMainNetwork.ADDRESS_BYTE_PREFIX,
    LitecoinTestNetwork.ADDRESS_BYTE_PREFIX,
]


SCRIPT_HASH_LIST = [
    BitcoinMainNetwork.SCRIPT_BYTE_PREFIX,
    BitcoinTestNetwork.SCRIPT_BYTE_PREFIX,
    LitecoinMainNetwork.SCRIPT_BYTE_PREFIX,
    LitecoinMainNetwork.SCRIPT_BYTE_PREFIX_2,
    LitecoinTestNetwork.SCRIPT_BYTE_PREFIX,
    LitecoinTestNetwork.SCRIPT_BYTE_PREFIX_2,
]
