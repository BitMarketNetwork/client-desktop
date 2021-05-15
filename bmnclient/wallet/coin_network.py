class CoinNetworkBase:
    PRIVATE_KEY = None

    @classmethod
    def from_prv_version(cls, version) -> "CoinNetworkBase":
        for net in (val for _, val in globals().items() if isinstance(val, type) and issubclass(val, cls) and val is not cls):
            if version == net.PRIVATE_KEY:
                return net


class BitcoinMainNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x00'
    SCRIPT_BYTE_PREFIX = b'\x05'
    BECH32_HRP = 'bc'
    PRIVATE_KEY = b'\x80'


class BitcoinTestNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x6f'
    SCRIPT_BYTE_PREFIX = b'\xc4'
    BECH32_HRP = 'tb'
    PRIVATE_KEY = b'\xef'


class LitecoinMainNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x30'
    SCRIPT_BYTE_PREFIX = b'\x05'
    SCRIPT_BYTE_PREFIX_2 = b'\x32'
    PRIVATE_KEY = b'\xB0'
    BECH32_HRP = 'ltc'


class LitecoinTestNetwork(CoinNetworkBase):
    ADDRESS_BYTE_PREFIX = b'\x6f'
    SCRIPT_BYTE_PREFIX = b'\xc4'
    SCRIPT_BYTE_PREFIX_2 = b'\x3A'
    PRIVATE_KEY = b'\xef'
    BECH32_HRP = 'tltc'


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

MAIN_NET_PREFIX_SET = [
    BitcoinMainNetwork.ADDRESS_BYTE_PREFIX,
    BitcoinMainNetwork.SCRIPT_BYTE_PREFIX,
    LitecoinMainNetwork.ADDRESS_BYTE_PREFIX,
    LitecoinMainNetwork.SCRIPT_BYTE_PREFIX,
    LitecoinMainNetwork.SCRIPT_BYTE_PREFIX_2,
]

TEST_NET_PREFIX_SET = [
    BitcoinTestNetwork.ADDRESS_BYTE_PREFIX,
    BitcoinTestNetwork.SCRIPT_BYTE_PREFIX,
    LitecoinTestNetwork.ADDRESS_BYTE_PREFIX,
    LitecoinTestNetwork.SCRIPT_BYTE_PREFIX,
    LitecoinTestNetwork.SCRIPT_BYTE_PREFIX_2,
]

MAIN_BECH_HRP_SET = [
    BitcoinMainNetwork.BECH32_HRP,
    LitecoinMainNetwork.BECH32_HRP,
]

TEST_BECH_HRP_SET = [
    BitcoinTestNetwork.BECH32_HRP,
    LitecoinTestNetwork.BECH32_HRP,
]
