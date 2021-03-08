# JOK++
from __future__ import annotations

from ..coins.coin import AbstractCoin
from ..logger import Logger


class ServerCoinParser:
    @classmethod
    def parse(cls, server_response: dict, coin: AbstractCoin) -> bool:
        try:
            offset = str(server_response["offset"])
            unverified_offset = str(server_response["unverified_offset"])
            unverified_hash = str(server_response["unverified_hash"])
            height = int(server_response["height"])
            verified_height = int(server_response["verified_height"])
            status = int(server_response["status"])
        except (KeyError, TypeError, ValueError) as e:
            Logger.getClassLogger(__name__, cls).exception(e)
            return False

        # TODO legacy order
        coin.status = status
        coin.unverifiedHash = unverified_hash
        coin.unverifiedOffset = unverified_offset
        coin.offset = offset
        coin.verifiedHeight = verified_height
        coin.height = height
        return True
