# JOK++
from __future__ import annotations

from typing import Optional


class TxModelInterface:
    # TODO
    pass


class AbstractTx:
    @property
    def model(self) -> Optional[TxModelInterface]:
        # TODO
        return None
