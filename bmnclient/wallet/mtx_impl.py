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
            *,
            coin: AbstractCoin,
            utxo_list: List[AbstractCoin.Tx.Utxo],
            tx_in: List[TxInput],
            tx_out: List[TxOutput]) -> None:
        self._coin = coin
        self._version = coin.Script.integerToBytes(0x01, 4)
        self._tx_in = tx_in
        self._tx_out = tx_out
        self._lock_time = self._coin.Script.integerToBytes(0, 4)

        if any([i.is_segwit for i in tx_in]):
            for i in self._tx_in:
                if not i.witness:
                    i.witness = b"\x00"

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    @property
    def name(self) -> str:
        v = Sha256DoubleDigest(self.serialize(with_segwit=False)).finalize()
        return v[::-1].hex()

    def serialize(self, *, with_segwit: bool = True) -> bytes:
        if with_segwit:
            witness_list = b"".join([w.witness for w in self._tx_in])
        else:
            witness_list = b""

        return b"".join([
            self._version,
            self._WITNESS_FLAG if witness_list else b"",

            self._coin.Script.integerToVarInt(len(self._tx_in)),
            b"".join(map(lambda i: i.serialize(), self._tx_in)),

            self._coin.Script.integerToVarInt(len(self._tx_out)),
            b"".join(map(lambda o: o.serialize(), self._tx_out)),

            witness_list,
            self._lock_time
        ])

    def sign(
            self,
            address: Bitcoin.Address,
            *,
            utxo_list: List[Bitcoin.Tx.Utxo]) -> bool:
        input_dict = {}
        for utxo in utxo_list:
            tx_input = \
                bytes.fromhex(utxo.name)[::-1] \
                + utxo.index.to_bytes(4, byteorder='little')
            input_dict[tx_input] = utxo.serialize()
            input_dict[tx_input]["segwit"] = utxo.address.type.value.isSegwit

        # Determine input indices to sign from input_dict (allows for
        # transaction batching)
        sign_inputs = [
            j for j, i in enumerate(self._tx_in) if i.utxoId in input_dict
        ]

        segwit_tx = self.is_segwit
        inputs_parameters = []
        if not sign_inputs:
            raise Exception
        for i in sign_inputs:
            tx_in = self._tx_in[i]
            # Create transaction object for preimage calculation
            tx_input = tx_in.utxoId
            segwit_input = input_dict[tx_input]["segwit"]
            tx_in.segwit_input = segwit_input

            # Use scriptCode for preimage calculation of transaction object:
            tx_in.script_sig = self._coin.Script.addressToScript(
                address,
                address.Type.PUBKEY_HASH)  # TODO SCRIPT_HASH?
            tx_in.script_sig_len = self._coin.Script.integerToVarInt(
                len(tx_in.script_sig))

            if segwit_input:
                tx_in.script_sig += input_dict[tx_input]["amount"] \
                    .to_bytes(8, byteorder='little')

            inputs_parameters.append((i, self._HASH_TYPE, segwit_input))

        preimages = self.calc_preimages(inputs_parameters)

        for hash_, (i, _, segwit_input) in zip(preimages, inputs_parameters):
            tx_in = self._tx_in[i]
            signature = address.privateKey.sign(hash_) + b'\x01'
            witness = (
                (b'\x02' if segwit_input else b'') +  # witness counter
                len(signature).to_bytes(1, byteorder='little') +
                signature +
                self._coin.Script.pushData(address.publicKey.data)
            )

            if segwit_input:
                tx_in.script_sig = b""
                tx_in.witness = witness
            else:
                tx_in.script_sig = witness
                tx_in.witness = b'\x00' if segwit_tx else b""
            tx_in.script_sig_len = self._coin.Script.integerToVarInt(
                len(tx_in.script_sig))
        return True

    def calc_preimages(
            self,
            inputs_parameters: List[Tuple[int, bytes, bool]]) \
            -> List[bytes]:
        input_count = self._coin.Script.integerToVarInt(len(self._tx_in))
        output_count = self._coin.Script.integerToVarInt(len(self._tx_out))
        output_block = b"".join([o.serialize() for o in self._tx_out])

        hash_prev_outs = Sha256DoubleDigest(
            b"".join([i.utxoId for i in self._tx_in])).finalize()
        hash_sequence = Sha256DoubleDigest(
            b"".join([i.sequence for i in self._tx_in])).finalize()
        hash_outputs = Sha256DoubleDigest(output_block).finalize()

        preimages = []
        for input_index, hash_type, segwit_input in inputs_parameters:
            # We can only handle hashType == 1:
            if hash_type != self._HASH_TYPE:
                raise ValueError('bit only support hashType of value 1')

            # Calculate pre hashes:
            if segwit_input:
                # BIP-143 preimage:
                hashed = Sha256Digest(
                    self._version +
                    hash_prev_outs +
                    hash_sequence +
                    self._tx_in[input_index].utxoId +
                    # scriptCode length
                    self._tx_in[input_index].script_sig_len +
                    # scriptCode (includes amount)
                    self._tx_in[input_index].script_sig +
                    self._tx_in[input_index].sequence +
                    hash_outputs +
                    self._lock_time +
                    hash_type
                ).finalize()
            else:
                hashed = Sha256Digest(
                    self._version +
                    input_count +
                    b"".join(
                        # TODO self._coin.Script.OpCode.OP_0
                        ti.utxoId + b"\0" + ti.sequence
                        for ti in itertools.islice(self._tx_in, input_index)
                    ) +
                    self._tx_in[input_index].utxoId +
                    # scriptCode length
                    self._tx_in[input_index].script_sig_len +
                    self._tx_in[input_index].script_sig +  # scriptCode
                    self._tx_in[input_index].sequence +
                    b"".join(
                        # TODO self._coin.Script.OpCode.OP_0
                        ti.utxoId + b"\0" + ti.sequence
                        for ti in itertools.islice(
                            self._tx_in,
                            input_index + 1,
                            None)
                    ) +
                    output_count +
                    output_block +
                    self._lock_time +
                    hash_type
                ).finalize()
            preimages.append(hashed)
        return preimages
