from __future__ import annotations

from typing import TYPE_CHECKING

from ..abstract import Coin

if TYPE_CHECKING:
    from typing import Optional, Sequence, Tuple
    from . import Bitcoin


class _TxFactory(Coin.TxFactory):
    from .mutable_tx import _MutableTx
    MutableTx = _MutableTx

    if TYPE_CHECKING:
        _coin: Bitcoin

    def _prepare(
            self,
            input_list: Sequence[Bitcoin.Tx.Utxo],
            output_list: Sequence[Tuple[Bitcoin.Address, int]],
            *,
            time: int = -1,
            is_dummy: bool) -> Optional[_TxFactory.MutableTx]:
        return self.MutableTx(
            self._coin,
            [
                self.MutableTx.Input(u, is_dummy=is_dummy)
                for u in input_list],
            [
                self.MutableTx.Output(a, amount=v, is_dummy=is_dummy)
                for a, v in output_list],
            is_dummy=is_dummy,
            time=time)
