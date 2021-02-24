# JOK++
from __future__ import annotations

from typing import Optional


class AbstractTxModel:
    # TODO
    pass


class AbstractTx:
    @property
    def model(self) -> Optional[AbstractTxModel]:
        # TODO
        return None
