from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

from ..abstract.coin import AbstractCoin
from ...crypto.digest import Sha256Digest, Sha256DoubleDigest
from ...crypto.secp256k1 import PrivateKey, PublicKey

if TYPE_CHECKING:
    from typing import Optional, Sequence, Tuple
    from . import Bitcoin


class _BitcoinMutableTxInput(AbstractCoin.TxFactory.MutableTx.Input):
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
        super().__init__(
            utxo,
            utxo_id_bytes=utxo_id_bytes,
            hash_type=1,  # SIGHASH_ALL
            sequence=sequence,
            **kwargs)

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
            else:
                signature = b"\x00" * PrivateKey.signatureMaxSize
            signature += self._coin.Script.integerToVarInt(self._hash_type)

            if self.isWitness:
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

    def __init__(
            self,
            address: Bitcoin.Address,
            amount: int,
            **kwargs) -> None:
        super().__init__(address, amount, **kwargs)
        try:
            script = self._coin.Script.addressToScript(self._address)
            self._script_bytes = \
                self._coin.Script.integerToVarInt(len(script)) \
                + script
        except TypeError:
            self._script_bytes = b""


class _BitcoinMutableTx(AbstractCoin.TxFactory.MutableTx):
    _VERSION_LENGTH = 4
    _LOCK_TIME_LENGTH = 4
    _WITNESS_HEADER = b"\x00\x01"

    Input = _BitcoinMutableTxInput
    Output = _BitcoinMutableTxOutput

    def __init__(
            self,
            coin: Bitcoin,
            input_list: Sequence[Input],
            output_list: Sequence[Output],
            *,
            lock_time: int = 0,
            **kwargs) -> None:
        super().__init__(
            coin,
            input_list,
            output_list,
            lock_time=lock_time,
            version=1,
            **kwargs)

    def _deriveName(self) -> Optional[str]:
        v = Sha256DoubleDigest(self.serialize(with_witness=False)).finalize()
        return v[::-1].hex()

    def _sign(self) -> bool:
        if self._is_dummy:
            hash_ = b"\x00" * Sha256Digest.size
            for current_input in self._input_list:
                if not current_input.sign(hash_):
                    return False
            return True

        input_count = self._coin.Script.integerToVarInt(
            len(self._input_list))
        output_count = self._coin.Script.integerToVarInt(
            len(self._output_list))
        if not input_count or not output_count:
            return False

        output_list = b"".join(
            o.amountBytes + o.scriptBytes
            for o in self._output_list)

        if self._is_witness:
            output_list_hash = Sha256DoubleDigest(output_list).finalize()

            hash_prevouts = b"".join(
                i.utxoIdBytes
                for i in self._input_list)
            hash_prevouts = Sha256DoubleDigest(hash_prevouts).finalize()

            hash_sequence = b"".join(
                i.sequenceBytes
                for i in self._input_list)
            hash_sequence = Sha256DoubleDigest(hash_sequence).finalize()
        else:
            output_list_hash = b""
            hash_prevouts = b""
            hash_sequence = b""

        for current_index, current_input in enumerate(self._input_list):
            digest = Sha256Digest()
            digest.update(self.versionBytes)

            if current_input.isWitness:
                digest.update(hash_prevouts)
                digest.update(hash_sequence)
                digest.update(current_input.utxoIdBytes)
                digest.update(current_input.scriptBytes)
                digest.update(current_input.amountBytes)
                digest.update(current_input.sequenceBytes)
                digest.update(output_list_hash)
            else:
                digest.update(input_count)
                for other_index, other_input in enumerate(self._input_list):
                    digest.update(other_input.utxoIdBytes)
                    if current_index == other_index:
                        digest.update(other_input.scriptBytes)
                    else:
                        digest.update(self._coin.Script.integerToVarInt(0))
                    digest.update(other_input.sequenceBytes)
                digest.update(output_count)
                digest.update(output_list)

            digest.update(self.lockTimeBytes)
            digest.update(current_input.hashTypeBytes)

            if not current_input.sign(digest.finalize()):
                return False
        return True

    def _serialize(self, *, with_witness: bool = True) -> bytes:
        try:
            input_list = \
                self._coin.Script.integerToVarInt(len(self._input_list)) \
                + b"".join(
                    i.utxoIdBytes + i.scriptSigBytes + i.sequenceBytes
                    for i in self._input_list)

            output_list = \
                self._coin.Script.integerToVarInt(len(self._output_list)) \
                + b"".join(
                    o.amountBytes + o.scriptBytes
                    for o in self._output_list)

            if with_witness and self._is_witness:
                witness_list = b"".join(
                    i.witnessBytes
                    for i in self._input_list)
            else:
                witness_list = b""

            return (
                self.versionBytes
                + (self._WITNESS_HEADER if witness_list else b"")
                + input_list
                + output_list
                + witness_list
                + self.lockTimeBytes)
        except TypeError:
            return b""

    @property
    def virtualSize(self) -> int:
        if self.isWitness:
            non_witness_size = len(self.serialize(with_witness=False))
            return ceil((3 * non_witness_size + self.rawSize) / 4)
        return self.rawSize


class _BitcoinTxFactory(AbstractCoin.TxFactory):
    MutableTx = _BitcoinMutableTx

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
                self.MutableTx.Output(a, v, is_dummy=is_dummy)
                for a, v in output_list],
            is_dummy=is_dummy)
