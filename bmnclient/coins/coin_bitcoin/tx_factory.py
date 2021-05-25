# JOK4
from __future__ import annotations

from typing import TYPE_CHECKING

from ..abstract.coin import AbstractCoin

if TYPE_CHECKING:
    from typing import Sequence
    from . import Bitcoin


class _BitcoinMutableTxInput(AbstractCoin.TxFactory.MutableTx.Input):
    _AMOUNT_LENGTH = 8
    _HASH_TYPE_LENGTH = 4
    _SEQUENCE_LENGTH = 4

    def __init__(
            self,
            utxo: Bitcoin.Tx.Utxo,
            *,
            sequence: int = 0xffffffff) -> None:
        utxo_id_bytes = \
            bytes.fromhex(utxo.name)[::-1] \
            + (utxo.coin.Script.integerToBytes(utxo.index, 4) or b"\x00" * 4)
        super().__init__(
            utxo,
            utxo_id_bytes=utxo_id_bytes,
            hash_type=1,  # SIGHASH_ALL
            sequence=sequence)

        # For P2WPKH witness program, the scriptCode is
        # 0x1976a914{20-byte-pubkey-hash}88ac.
        if self._utxo.scriptType in (
                self._coin.Script.Type.P2WPKH,
                self._coin.Script.Type.P2SH_P2WPKH
        ):
            script = self._coin.Script.addressToScript(
                self._utxo.address,
                self._coin.Script.Type.P2PKH)
        else:
            script = self._coin.Script.addressToScript(
                self._utxo.address,
                self._utxo.scriptType)
        try:
            self._script_bytes = \
                self._coin.Script.integerToVarInt(len(script)) \
                + script
        except TypeError:
            self._script_bytes = self._coin.Script.integerToVarInt(0)

    def sign(self, hash_: bytes) -> bool:
        private_key = self._utxo.address.privateKey
        if not private_key or not (1 <= self._hash_type < 0xfd):
            return False
        public_key_data = private_key.publicKey.data

        try:
            signature = private_key.sign(hash_)
            signature += self._coin.Script.integerToVarInt(self._hash_type)

            if self.isSegwit:
                if self.utxo.scriptType == self._coin.Script.Type.P2SH_P2WPKH:
                    script_sig = self._coin.Script.addressToScript(
                        self.utxo.address,
                        self._coin.Script.Type.P2WPKH)
                    script_sig = self._coin.Script.pushData(script_sig)
                else:
                    script_sig = b""

                # A witness field starts with a var_int to indicate the number
                # of stack items for the txin. It is followed by stack items,
                # with each item starts with a var_int to indicate the length.
                wd = self._coin.Script.integerToVarInt(2)

                # 1
                wd += self._coin.Script.integerToVarInt(len(signature))
                wd += signature

                # 2
                wd += self._coin.Script.integerToVarInt(len(public_key_data))
                wd += public_key_data
            else:
                if self.utxo.scriptType == self._coin.Script.Type.P2PK:
                    script_sig = self._coin.Script.pushData(signature)
                else:
                    script_sig = self._coin.Script.pushData(signature)
                    script_sig += self._coin.Script.pushData(public_key_data)

                # A non-witness program (defined hereinafter) txin MUST be
                # associated with an empty witness field, represented by a 0x00.
                wd = self._coin.Script.integerToVarInt(0)

            # noinspection PyAttributeOutsideInit
            self._script_sig_bytes = \
                self._coin.Script.integerToVarInt(len(script_sig)) \
                + script_sig
            # noinspection PyAttributeOutsideInit
            self._witness_bytes = wd
        except TypeError:
            # noinspection PyAttributeOutsideInit
            self._script_sig_bytes = b""
            # noinspection PyAttributeOutsideInit
            self._witness_bytes = b""
            return False

        return True


class _BitcoinMutableTxOutput(AbstractCoin.TxFactory.MutableTx.Output):
    _AMOUNT_LENGTH = 8

    def __init__(self, address: Bitcoin.Address, amount: int) -> None:
        super().__init__(address, amount)
        try:
            script = self._coin.Script.addressToScript(self._address)
            self._script_bytes = \
                self._coin.Script.integerToVarInt(len(script)) \
                + script
        except TypeError:
            self._script_bytes = b""


class _BitcoinMutableTx(AbstractCoin.TxFactory.MutableTx):
    Input = _BitcoinMutableTxInput
    Output = _BitcoinMutableTxOutput


class _BitcoinTxFactory(AbstractCoin.TxFactory):
    MutableTx = _BitcoinMutableTx
