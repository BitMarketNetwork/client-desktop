from __future__ import annotations

from functools import cached_property
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
            mtx: Bitcoin.TxFactory.MutableTx,
            *,
            utxo: Bitcoin.Tx.Utxo,
            sequence: int = 0xffffffff,
            **kwargs) -> None:
        super().__init__(
            mtx,
            utxo=utxo,
            hash_type=1,  # SIGHASH_ALL
            sequence=sequence,
            **kwargs)

    @cached_property
    def scriptBytes(self) -> bytes:
        # For P2WPKH witness program, the scriptCode is
        # 0x1976a914{20-byte-pubkey-hash}88ac.
        if self._utxo.scriptType in (
                self._utxo.address.Script.Type.P2WPKH,
                self._utxo.address.Script.Type.P2SH_P2WPKH
        ):
            script = self._utxo.address.Script.addressToScript(
                self._utxo.address,
                self._utxo.address.Script.Type.P2PKH)
        else:
            script = self._utxo.address.Script.addressToScript(
                self._utxo.address,
                self._utxo.scriptType)
        if not script:
            return self._utxo.address.Script.integerToVarInt(0)
        return (
                self._utxo.address.Script.integerToVarInt(len(script))
                + script)

    @cached_property
    def utxoIdBytes(self) -> bytes:
        index = (
                self._utxo.address.Script.integerToBytes(self._utxo.index, 4)
                or b"\x00" * 4)
        return bytes.fromhex(self._utxo.name)[::-1] + index

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
        script = self._address.Script
        try:
            if not self._is_dummy:
                signature = private_key.sign(hash_)
                if not signature:
                    return False
            else:
                signature = b"\x00" * PrivateKey.signatureMaxSize
            signature += script.integerToVarInt(self._hash_type)

            if self.isWitness:
                if self.utxo.scriptType == script.Type.P2SH_P2WPKH:
                    script_sig = script.addressToScript(
                        self.utxo.address,
                        script.Type.P2WPKH)
                    if script_sig is None:
                        return False
                    script_sig = script.pushData(script_sig)
                else:
                    script_sig = b""

                # A witness field starts with a var_int to indicate the number
                # of stack items for the txin. It is followed by stack items,
                # with each item starts with a var_int to indicate the length.
                wd = script.integerToVarInt(2)

                # 1
                wd += script.integerToVarInt(len(signature))
                wd += signature

                # 2
                wd += script.integerToVarInt(len(public_key_data))
                wd += public_key_data
            else:
                if self.utxo.scriptType == script.Type.P2PK:
                    script_sig = script.pushData(signature)
                else:
                    script_sig = script.pushData(signature)
                    script_sig += script.pushData(public_key_data)

                # A non-witness program (defined hereinafter) txin MUST be
                # associated with an empty witness field, represented by a 0x00.
                wd = script.integerToVarInt(0)
        except TypeError:
            return False

        try:
            # noinspection PyAttributeOutsideInit
            self._script_sig_bytes = (
                    script.integerToVarInt(len(script_sig))
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

    def __init__(self, mtx: Bitcoin.TxFactory.MutableTx, **kwargs) -> None:
        super().__init__(mtx, **kwargs)

    @cached_property
    def scriptBytes(self) -> bytes:
        script = self._address.Script.addressToScript(self._address)
        if not script:
            return self._address.Script.integerToVarInt(0)
        return (
                self._address.Script.integerToVarInt(len(script))
                + script)
