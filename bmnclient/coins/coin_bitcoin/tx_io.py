from __future__ import annotations

from typing import TYPE_CHECKING

from ..abstract import Coin
from ...crypto.secp256k1 import PrivateKey, PublicKey

if TYPE_CHECKING:
    from . import Bitcoin


class _MutableInput(Coin.TxFactory.MutableTx.Input):
    _AMOUNT_LENGTH = 8
    _HASH_TYPE_LENGTH = 4
    _SEQUENCE_LENGTH = 4

    def __init__(
            self,
            utxo: Bitcoin.Tx.Utxo,
            *,
            sequence: int = 0xffffffff,
            **kwargs) -> None:
        utxo_id_bytes = \
            bytes.fromhex(utxo.name)[::-1] \
            + (utxo.coin.Script.integerToBytes(utxo.index, 4) or b"\x00" * 4)

        # For P2WPKH witness program, the scriptCode is
        # 0x1976a914{20-byte-pubkey-hash}88ac.
        if utxo.scriptType in (
                utxo.coin.Script.Type.P2WPKH,
                utxo.coin.Script.Type.P2SH_P2WPKH
        ):
            script = utxo.coin.Script.addressToScript(
                utxo.address,
                utxo.coin.Script.Type.P2PKH)
        else:
            script = utxo.coin.Script.addressToScript(
                utxo.address,
                utxo.scriptType)
        if script:
            script_bytes = (
                    utxo.coin.Script.integerToVarInt(len(script))
                    + script)
        else:
            script_bytes = utxo.coin.Script.integerToVarInt(0)

        super().__init__(
            utxo,
            utxo_id_bytes=utxo_id_bytes,
            hash_type=1,  # SIGHASH_ALL
            sequence=sequence,
            script_bytes=script_bytes,
            **kwargs)

    def sign(self, hash_: bytes) -> bool:
        if not self._is_dummy:
            private_key = self._utxo.address.privateKey
            if not private_key or not (1 <= self._hash_type < 0xfd):
                return False
            public_key_data = private_key.publicKey.data
        else:
            private_key = None
            if (
                    self._utxo.address.publicKey
                    and not self._utxo.address.publicKey.isCompressed
            ):
                # rare case
                public_key_data = b"\x00" * PublicKey.uncompressedSize
            else:
                public_key_data = b"\x00" * PublicKey.compressedSize

        try:
            if not self._is_dummy:
                signature = private_key.sign(hash_)
                if not signature:
                    return False
            else:
                signature = b"\x00" * PrivateKey.signatureMaxSize
            signature += self._coin.Script.integerToVarInt(self._hash_type)

            if self.isWitness:
                if self.utxo.scriptType == self._coin.Script.Type.P2SH_P2WPKH:
                    script_sig = self._coin.Script.addressToScript(
                        self.utxo.address,
                        self._coin.Script.Type.P2WPKH)
                    if script_sig is None:
                        return False
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
        except TypeError:
            return False

        try:
            # noinspection PyAttributeOutsideInit
            self._script_sig_bytes = (
                    self._coin.Script.integerToVarInt(len(script_sig))
                    + script_sig)
            # noinspection PyAttributeOutsideInit
            self._witness_bytes = wd
            return True
        except TypeError:
            # noinspection PyAttributeOutsideInit
            self._script_sig_bytes = b""
            # noinspection PyAttributeOutsideInit
            self._witness_bytes = b""
            return False


class _MutableOutput(Coin.TxFactory.MutableTx.Output):
    _AMOUNT_LENGTH = 8

    def __init__(
            self,
            address: Bitcoin.Address,
            amount: int,
            **kwargs) -> None:
        script = address.coin.Script.addressToScript(address)
        if script:
            script_bytes = (
                    address.coin.Script.integerToVarInt(len(script))
                    + script)
        else:
            script_bytes = address.coin.Script.integerToVarInt(0)
        super().__init__(
            address.coin,
            address,
            amount=amount,
            script_bytes=script_bytes,
            **kwargs)
