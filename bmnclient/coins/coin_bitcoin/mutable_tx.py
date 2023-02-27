from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

from ..abstract import Coin
from ...crypto.digest import Sha256Digest, Sha256DoubleDigest

if TYPE_CHECKING:
    from . import Bitcoin


class _MutableTx(Coin.TxFactory.MutableTx):
    _VERSION_LENGTH = 4
    _LOCK_TIME_LENGTH = 4
    _WITNESS_HEADER = b"\x00\x01"

    from .mutable_tx_io import _MutableInput, _MutableOutput
    Input = _MutableInput
    Output = _MutableOutput

    def __init__(self, coin: Bitcoin, *, lock_time: int = 0, **kwargs) -> None:
        super().__init__(coin, lock_time=lock_time, version=1, **kwargs)

    def _deriveName(self) -> str | None:
        v = Sha256DoubleDigest(self.raw(with_witness=False)).finalize()
        return v[::-1].hex()

    def _sign(self) -> bool:
        if self._is_dummy:
            hash_ = b"\x00" * Sha256Digest.size
            for current_input in self._input_list:
                if not current_input.sign(hash_):
                    return False
            return True

        input_count = self._coin.Address.Script.integerToVarInt(
            len(self._input_list))
        output_count = self._coin.Address.Script.integerToVarInt(
            len(self._output_list))
        if not input_count or not output_count:
            return False

        output_list = b"".join(
            o.amountBytes + o.scriptBytes
            for o in self._output_list)

        if self.isWitness:
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
                        digest.update(
                            self._coin.Address.Script.integerToVarInt(0))
                    digest.update(other_input.sequenceBytes)
                digest.update(output_count)
                digest.update(output_list)

            digest.update(self.lockTimeBytes)
            digest.update(current_input.hashTypeBytes)

            if not current_input.sign(digest.finalize()):
                return False
        return True

    def _raw(self, *, with_witness: bool = True, **_) -> bytes:
        try:
            input_list = (
                self._coin.Address.Script.integerToVarInt(
                    len(self._input_list))
                + b"".join(
                    i.utxoIdBytes + i.scriptSigBytes + i.sequenceBytes
                    for i in self._input_list)
            )

            output_list = (
                self._coin.Address.Script.integerToVarInt(
                    len(self._output_list))
                + b"".join(
                    o.amountBytes + o.scriptBytes
                    for o in self._output_list)
            )

            if with_witness and self.isWitness:
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
            non_witness_size = len(self.raw(with_witness=False))
            return ceil((3 * non_witness_size + self.rawSize) / 4)
        return self.rawSize
