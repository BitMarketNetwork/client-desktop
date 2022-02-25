from __future__ import annotations

from typing import TYPE_CHECKING

from ..abstract import Coin
from ..coin_bitcoin import Bitcoin

if TYPE_CHECKING:
    from typing import Final


class _Address(Bitcoin.Address):
    _PUBKEY_HASH_PREFIX_LIST = ("L",)
    _SCRIPT_HASH_PREFIX_LIST = ("M",)
    _HRP = "ltc"

    class Type(Coin.Address.Type):
        UNKNOWN: Final = \
            Bitcoin.Address.Type.UNKNOWN.value
        PUBKEY_HASH: Final = \
            Bitcoin.Address.Type.PUBKEY_HASH.value.copy(version=0x30)
        SCRIPT_HASH: Final = \
            Bitcoin.Address.Type.SCRIPT_HASH.value.copy(version=0x32)
        WITNESS_V0_KEY_HASH: Final = \
            Bitcoin.Address.Type.WITNESS_V0_KEY_HASH.value
        WITNESS_V0_SCRIPT_HASH: Final = \
            Bitcoin.Address.Type.WITNESS_V0_SCRIPT_HASH.value
        WITNESS_UNKNOWN: Final = \
            Bitcoin.Address.Type.WITNESS_UNKNOWN.value
        DEFAULT = WITNESS_V0_KEY_HASH
