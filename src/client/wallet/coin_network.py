

import logging
from typing import List, Optional, Tuple

import PySide2.QtCore as qt_core

from .. import meta

log = logging.getLogger(__name__)


class CoinNetworkBase:
    EX_PREFIX_PRV = None
    EX_PREFIX_PUB = None
    PRIVATE_KEY = None
    # just for tests
    TITLE = "abstact"
    #

    def __str__(self):
        return self.__class__.__name__

    @meta.classproperty
    def all(cls) -> List["CoinNetworkBase"]:  # pylint: disable=no-self-argument
        return (val for _, val in globals().items() if isinstance(val, type) and issubclass(val, cls) and val is not cls)

    @meta.classproperty
    def bech32_hrps(cls) -> List[str]:  # pylint: disable=no-self-argument
        return [me.BECH32_HRP for me in cls.all]

    @classmethod
    def from_prv_version(cls, version) -> "CoinNetworkBase":
        for net in cls.all:
            if version == net.PRIVATE_KEY:
                return net

    @classmethod
    def from_address(cls, address: str) -> "CoinNetworkBase":
        if address and isinstance(address, str):
            from .key import AddressString
            # TODO: not segwit
            segwit = AddressString.is_segwit(address)
            if segwit:
                for net in cls.all:
                    if address.startswith(net.BECH32_HRP):
                        return net

    @classmethod
    def from_ex_prefix(cls, pref: int) -> Tuple["CoinNetworkBase", Optional[bool]]:
        """
        returns net, bool[prv else pub] or None , None
        """
        net = next((net for net in cls.all if net.EX_PREFIX_PRV == pref), None)
        if net is None:
            net = next(
                (net for net in cls.all if net.EX_PREFIX_PUB == pref), None)
            if net is None:
                return None, None
            return net, False
        return net, True


class BitcoinMainNetwork(CoinNetworkBase):
    EX_PREFIX_PRV = 0x0488ADE4
    EX_PREFIX_PUB = 0x0488B21E
    ADDRESS_BYTE_PREFIX = b'\x00'
    SCRIPT_BYTE_PREFIX = b'\x05'
    BECH32_HRP = 'bc'
    ADDRESS_PREFIX = '1'
    SCRIPT_ADDRESS_PREFIX = '3'
    PRIVATE_KEY = b'\x80'
    TITLE = "main"


class BitcoinTestNetwork(CoinNetworkBase):
    EX_PREFIX_PRV = 0x04358394
    EX_PREFIX_PUB = 0x043587CF
    ADDRESS_BYTE_PREFIX = b'\x6f'
    SCRIPT_BYTE_PREFIX = b'\xc4'
    BECH32_HRP = 'tb'
    ADDRESS_PREFIX = 'm'
    ADDRESS_PREFIX_2 = 'n'
    SCRIPT_ADDRESS_PREFIX = '2'
    PRIVATE_KEY = b'\xef'
    TITLE = "test"


class BitcoinRegTestNetwork(CoinNetworkBase):
    BECH32_HRP = 'bcrt'
    TITLE = "regtest"


class LitecoinMainNetwork(CoinNetworkBase):
    EX_PREFIX_PRV = 0x019da462
    EX_PREFIX_PUB = 0x019da462
    ADDRESS_BYTE_PREFIX = b'\x30'
    SCRIPT_BYTE_PREFIX = b'\x05'
    SCRIPT_BYTE_PREFIX_2 = b'\x32'
    PRIVATE_KEY = b'\xB0'
    BECH32_HRP = 'ltc'


class LitecoinTestNetwork(CoinNetworkBase):
    EX_PREFIX_PRV = 0x0436ef7d
    EX_PREFIX_PUB = 0x0436f6e1
    ADDRESS_BYTE_PREFIX = b'\x6f'
    SCRIPT_BYTE_PREFIX = b'\xc4'
    SCRIPT_BYTE_PREFIX_2 = b'\x3A'
    PRIVATE_KEY = b'\xef'
    BECH32_HRP = 'tltc'


ADDRESS_PREFIX_LIST = (BitcoinMainNetwork.ADDRESS_PREFIX,
                       BitcoinMainNetwork.SCRIPT_ADDRESS_PREFIX,
                       BitcoinTestNetwork.ADDRESS_PREFIX,
                       BitcoinTestNetwork.ADDRESS_PREFIX_2,
                       BitcoinTestNetwork.SCRIPT_ADDRESS_PREFIX,
                       )

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
