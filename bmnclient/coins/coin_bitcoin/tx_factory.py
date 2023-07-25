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
        is_dummy: bool,
    ) -> Optional[_TxFactory.MutableTx]:
        mtx = self.MutableTx(self._coin, time=time, is_dummy=is_dummy)
        for utxo in input_list:
            mtx.inputList.append(dict(utxo=utxo, is_dummy=is_dummy))
        for address, amount in output_list:
            mtx.outputList.append(
                dict(address=address, amount=amount, is_dummy=is_dummy)
            )
        return mtx
