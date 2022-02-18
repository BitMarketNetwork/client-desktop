from __future__ import annotations

from typing import TYPE_CHECKING

from .tx import _MutableTx
from ..abstract import Coin

if TYPE_CHECKING:
    from typing import Optional, Sequence, Tuple
    from . import Bitcoin


class _TxFactory(Coin.TxFactory):
    MutableTx = _MutableTx

    def _prepare(
            self,
            input_list: Sequence[Bitcoin.Tx.Utxo],
            output_list: Sequence[Tuple[Bitcoin.Address, int]],
            *,
            is_dummy: bool) \
            -> Optional[Bitcoin.TxFactory.MutableTx]:
        return self.MutableTx(
            self._coin,
            [
                self.MutableTx.Input(u, is_dummy=is_dummy)
                for u in input_list],
            [
                self.MutableTx.Output(a, amount=v, is_dummy=is_dummy)
                for a, v in output_list],
            is_dummy=is_dummy)
