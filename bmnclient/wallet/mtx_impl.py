from __future__ import annotations

from typing import TYPE_CHECKING

from ..crypto.digest import Sha256Digest, Sha256DoubleDigest
from ..coins.coin_bitcoin import Bitcoin

if TYPE_CHECKING:
    from typing import List, Tuple


class Mtx(Bitcoin.TxFactory.MutableTx):
    _HASH_TYPE = 0x01.to_bytes(4, byteorder='little')
    _WITNESS_FLAG = b"\x00\x01"

    def __init__(
            self,
            coin: Bitcoin,
            tx_in: List[Mtx.Input],
            tx_out: List[Mtx.Output],
            *,
            lock_time: int = 0) -> None:
        super().__init__(coin)
        self._version = coin.Script.integerToBytes(0x01, 4)
        self._tx_in = tx_in
        self._tx_out = tx_out
        self._lock_time = self._coin.Script.integerToBytes(lock_time, 4)

        self._is_segwit = False
        for i in tx_in:
            if i.isSegwit:
                self._is_segwit = True
                break

    @property
    def name(self) -> str:
        v = Sha256DoubleDigest(self.serialize(with_segwit=False)).finalize()
        return v[::-1].hex()

    def serialize(self, *, with_segwit: bool = True) -> bytes:
        if with_segwit and self._is_segwit:
            witness_list = b"".join([w.witnessBytes for w in self._tx_in])
        else:
            witness_list = b""

        input_list = b"".join([
            i.utxoIdBytes + i.scriptSigBytes + i.sequenceBytes
            for i in self._tx_in])

        return b"".join([
            self._version,
            self._WITNESS_FLAG if witness_list else b"",

            self._coin.Script.integerToVarInt(len(self._tx_in)),
            input_list,

            self._coin.Script.integerToVarInt(len(self._tx_out)),
            b"".join(map(lambda o: o.amountBytes + o.scriptBytes, self._tx_out)),

            witness_list,
            self._lock_time
        ])

    def sign(self) -> bool:
        for hash_, tx_in in self.calc_preimages():
            tx_in.sign(hash_, 1)
        return True

    def calc_preimages(self) -> List[Tuple[bytes, Mtx.Input]]:
        output_block = b"".join([o.amountBytes + o.scriptBytes for o in self._tx_out])

        preimages = []
        for index, tx_in in enumerate(self._tx_in):
            hash = Sha256Digest()
            hash.update(self._version)

            if tx_in.isSegwit:
                hash.update(Sha256DoubleDigest(
                    b"".join([i.utxoIdBytes for i in self._tx_in])).finalize())
                hash.update(Sha256DoubleDigest(
                    b"".join([i.sequenceBytes for i in self._tx_in])).finalize())
                hash.update(
                    tx_in.utxoIdBytes +
                    tx_in.scriptBytes +
                    tx_in.amountBytes +
                    tx_in.sequenceBytes +
                    Sha256DoubleDigest(output_block).finalize()
                )
            else:
                hash.update(self._coin.Script.integerToVarInt(len(self._tx_in)))
                for i, tx_in2 in enumerate(self._tx_in):
                    hash.update(tx_in2.utxoIdBytes)
                    if i != index:
                        hash.update(self._coin.Script.integerToVarInt(0))
                    else:
                        hash.update(tx_in2.scriptBytes)
                    hash.update(tx_in2.sequenceBytes)
                hash.update(self._coin.Script.integerToVarInt(len(self._tx_out)))
                hash.update(output_block)

            hash.update(self._lock_time)
            hash.update(self._HASH_TYPE)
            hash = hash.finalize()
            print(Sha256Digest(hash).finalize().hex())
            preimages.append((hash, tx_in))
        return preimages
