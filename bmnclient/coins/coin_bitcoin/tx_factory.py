# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..abstract.coin import AbstractCoin

if TYPE_CHECKING:
    from . import Bitcoin


class _BitcoinMutableTxInput(AbstractCoin.TxFactory.MutableTx.Input):
    def __init__(
            self,
            utxo: Bitcoin.Tx.Utxo,
            *,
            sequence: int = 0xffffffff) -> None:
        utxo_id = bytes.fromhex(utxo.name)[::-1]
        utxo_id += (
                utxo.coin.Script.integerToBytes(utxo.index, 4)
                or b"\x00" * 4)
        super().__init__(utxo, utxo_id, sequence=sequence)

class _BitcoinMutableTxOutput(AbstractCoin.TxFactory.MutableTx.Output):
    @property
    def amountBytes(self) -> bytes:
        return self._coin.Script.integerToBytes(self._amount, 8) or b"\x00" * 8

    def _createSerializedData(self) -> bytes:
        script = self._coin.Script.addressToScript(self._address)
        if script:
            script_length = self._coin.Script.integerToVarInt(len(script))
            if script_length:
                return self.amountBytes + script_length + script
        return b""


class _BitcoinMutableTx(AbstractCoin.TxFactory.MutableTx):
    Input = _BitcoinMutableTxInput
    Output = _BitcoinMutableTxOutput


class _BitcoinTxFactory(AbstractCoin.TxFactory):
    MutableTx = _BitcoinMutableTx
