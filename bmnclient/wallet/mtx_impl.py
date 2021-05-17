from __future__ import annotations

import itertools
import logging
from typing import TYPE_CHECKING

from . import constants, util
from ..coins.abstract.script import AbstractScript as Script  # TODO tmp
from ..crypto.digest import DoubleSha512Digest, Hash160Digest

if TYPE_CHECKING:
    from typing import List, Tuple
    from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class TxEntity:
    def __init__(self, address: str):
        self._address = address
        self.amount = None

    @property
    def amount_int(self) -> int:
        if isinstance(self.amount, bytes):
            return int.from_bytes(self.amount, "little")
        return self.amount

    @property
    def address(self) -> str:
        return self._address

    def __eq__(self, other: TxEntity):
        return (
                isinstance(other, self.__class__)
                and self._address == other._address
        )


class TxInput(TxEntity):
    __slots__ = ('script_sig', 'script_sig_len', 'tx_id', 'tx_index', 'witness',
                 'amount', 'sequence', 'segwit_input')

    def __init__(
            self,
            script_sig,
            tx_id,
            tx_index,
            witness=b'',
            amount=None,
            sequence=constants.SEQUENCE,
            segwit_input=False,
            address: str = None):
        super().__init__(address)

        self.script_sig = script_sig
        self.script_sig_len = Script.integerToVarInt(len(script_sig))
        self.tx_id = tx_id
        self.tx_index = tx_index
        self.witness = witness
        self.amount = amount
        self.sequence = sequence
        self.segwit_input = segwit_input

    def __eq__(self, other: TxInput):
        if not super().__eq__(other):
            return False
        return (self.script_sig == other.script_sig and
                self.script_sig_len == other.script_sig_len and
                self.tx_id == other.tx_id and
                self.tx_index == other.tx_index and
                self.witness == other.witness and
                self.amount == other.amount and
                self.sequence == other.sequence and
                self.segwit_input == other.segwit_input)

    def __bytes__(self) -> bytes:
        return b''.join([
            self.tx_id,
            self.tx_index,
            self.script_sig_len,
            self.script_sig,
            self.sequence
        ])

    def is_segwit(self) -> bool:
        return self.segwit_input or self.witness


class TxOutput(TxEntity):
    __slots__ = ('amount', 'script_pubkey_len', 'script_pubkey')

    def __init__(self, amount, script_pubkey, address: str = None):
        super().__init__(address)
        self.amount = amount
        self.script_pubkey = script_pubkey
        self.script_pubkey_len = Script.integerToVarInt(len(script_pubkey))

    def __eq__(self, other: TxOutput):
        if not super().__eq__(other):
            return False
        return (self.amount == other.amount and
                self.script_pubkey == other.script_pubkey and
                self.script_pubkey_len == other.script_pubkey_len)

    def __bytes__(self) -> bytes:
        return b''.join([
            self.amount,
            self.script_pubkey_len,
            self.script_pubkey
        ])


class NoInputsToSignError(Exception):
    pass


class Mtx:
    def __init__(
            self,
            coin: AbstractCoin,
            version: bytes,
            tx_in: List[TxInput],
            tx_out: List[TxOutput],
            lock_time: bytes) -> None:
        self._coin = coin
        segwit_tx = any([i.segwit_input or i.witness for i in tx_in])
        self.version = version
        self.TxIn = tx_in
        if segwit_tx:
            for i in self.TxIn:
                i.witness = i.witness if i.witness else b'\x00'
        self.TxOut = tx_out
        self.lock_time = lock_time

    def __bytes__(self) -> bytes:
        inp = Script.integerToVarInt(len(self.TxIn)) + \
            b''.join(map(bytes, self.TxIn))
        out = Script.integerToVarInt(len(self.TxOut)) + \
            b''.join(map(bytes, self.TxOut))
        wit = b''.join([w.witness for w in self.TxIn])
        return b''.join([
            self.version,
            constants.WIT_MARKER if wit else b'',
            constants.WIT_FLAG if wit else b'',
            inp,
            out,
            wit,
            self.lock_time
        ])

    def __eq__(self, other) -> bool:
        return (self.version == other.version and
                self.TxIn == other.TxIn and
                self.TxOut == other.TxOut and
                self.lock_time == other.lock_time)

    def __hash__(self) -> int:
        return hash((self.to_hex(), ))

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    def legacy_repr(self) -> bytes:
        inp = Script.integerToVarInt(len(self.TxIn)) + \
            b''.join(map(bytes, self.TxIn))
        out = Script.integerToVarInt(len(self.TxOut)) + \
            b''.join(map(bytes, self.TxOut))
        return b''.join([
            self.version,
            inp,
            out,
            self.lock_time
        ])

    def to_hex(self) -> str:
        return util.bytes_to_hex(bytes(self))

    @classmethod
    def make(
            cls,
            coin: AbstractCoin,
            utxo_list: List[AbstractCoin.Tx.Utxo],
            outputs: List[Tuple[str, int]]):
        version = constants.VERSION_1
        lock_time = constants.LOCK_TIME
        outputs = construct_outputs(outputs)

        # Optimize for speed, not memory, by pre-computing values.
        inputs = []
        for utxo in utxo_list:
            script_sig = b''  # empty scriptSig for new unsigned transaction.
            tx_id = util.hex_to_bytes(utxo.name)[::-1]
            tx_index = utxo.index.to_bytes(4, byteorder='little')
            amount = int(utxo.amount).to_bytes(8, byteorder='little')
            assert utxo.address
            inputs.append(TxInput(
                script_sig,
                tx_id,
                tx_index,
                amount=amount,
                segwit_input=utxo.segwit,
                address=utxo.address.name))
        out = cls(coin, version, inputs, outputs, lock_time)
        out.utxo_list = utxo_list
        return out

    @property
    def in_amount(self) -> int:
        return sum(inc.amount_int for inc in self.TxIn)

    @property
    def out_amount(self) -> int:
        return sum(out.amount_int for out in self.TxOut)

    @property
    def feeAmount(self) -> int:
        return self.in_amount - self.out_amount

    @classmethod
    def is_segwit(cls, tx) -> bool:
        if isinstance(tx, cls):
            tx = bytes(tx)
        elif not isinstance(tx, bytes):
            tx = util.hex_to_bytes(tx)
        return tx[4:6] == constants.WIT_MARKER + constants.WIT_FLAG

    @property
    def id(self) -> str:
        return util.bytes_to_hex(
            DoubleSha512Digest(self.legacy_repr()).finalize()[::-1])

    def sign(self, private_key: PrivateKey, *, utxo_list: List = None) -> str:
        input_dict = {}
        try:
            for utxo in (utxo_list or self.utxo_list):
                tx_input = \
                    util.hex_to_bytes(utxo.name)[::-1] \
                    + utxo.index.to_bytes(4, byteorder='little')
                input_dict[tx_input] = utxo.serialize()
                input_dict[tx_input]["segwit"] = utxo.segwit  # TODO tmp
        except TypeError:
            raise TypeError('please provide as unspent at least all inputs to '
                            'be signed with the function call in a list')
        # Determine input indices to sign from input_dict (allows for
        # transaction batching)
        sign_inputs = [
            j for j, i in enumerate(self.TxIn)
            if i.tx_id + i.tx_index in input_dict
        ]

        segwit_tx = Mtx.is_segwit(self)
        public_key = private_key.publicKey
        public_key_push = util.script_push(len(public_key.data))
        hash_type = constants.HASH_TYPE
        inputs_parameters = []
        input_script_field = [
            self.TxIn[i].script_sig for i in range(len(self.TxIn))]
        if not sign_inputs:
            raise NoInputsToSignError()
        for i in sign_inputs:
            tx_in = self.TxIn[i]
            # Create transaction object for preimage calculation
            tx_input = tx_in.tx_id + tx_in.tx_index
            segwit_input = input_dict[tx_input]['segwit']
            tx_in.segwit_input = segwit_input

            script_code = util.address_to_scriptpubkey(
                private_key.to_address("p2pkh"))
            script_code_len = util.int_to_varint(len(script_code))

            # Use scriptCode for preimage calculation of transaction object:
            tx_in.script_sig = script_code
            tx_in.script_sig_len = script_code_len

            if segwit_input:
                try:
                    tx_in.script_sig += input_dict[tx_input]['amount']\
                        .to_bytes(8, byteorder='little')

                    # For partially signed Segwit transactions the signatures
                    # must be extracted from the witnessScript field:
                    input_script_field[i] = tx_in.witness
                except AttributeError:
                    raise ValueError(
                        'cannot sign a segwit input when the input\'s amount is'
                        ' unknown. Maybe no network connection or the input is '
                        'already spent? Then please provide all inputs to sign '
                        'as `UTXO` objects to the function call')

            inputs_parameters.append([i, hash_type, segwit_input])

        preimages = self.calc_preimages(inputs_parameters)

        for hash_, (i, _, segwit_input) in zip(preimages, inputs_parameters):
            tx_in = self.TxIn[i]
            signature = private_key.sign(hash_) + b'\x01'
            if True:
                witness = (
                    (b'\x02' if segwit_input else b'') +  # witness counter
                    len(signature).to_bytes(1, byteorder='little') +
                    signature +
                    public_key_push +
                    public_key.data
                )

                script_sig = b'' if segwit_input else witness
                witness = witness if segwit_input else (
                    b'\x00' if segwit_tx else b'')

            # Providing the signature(s) to the input
            tx_in.script_sig = script_sig
            tx_in.script_sig_len = Script.integerToVarInt(len(script_sig))
            tx_in.witness = witness
        return self.to_hex()

    def calc_preimages(self, inputs_parameters) -> List:
        input_count = Script.integerToVarInt(len(self.TxIn))
        output_count = Script.integerToVarInt(len(self.TxOut))
        output_block = b''.join([bytes(o) for o in self.TxOut])

        hash_prev_outs = DoubleSha512Digest(
            b''.join([i.tx_id+i.tx_index for i in self.TxIn])).finalize()
        hash_sequence = DoubleSha512Digest(
            b''.join([i.sequence for i in self.TxIn])).finalize()
        hash_outputs = DoubleSha512Digest(output_block).finalize()

        preimages = []
        for input_index, hash_type, segwit_input in inputs_parameters:
            # We can only handle hashType == 1:
            if hash_type != constants.HASH_TYPE:
                raise ValueError('bit only support hashType of value 1')
            # Calculate pre hashes:
            if segwit_input:
                # BIP-143 preimage:
                hashed = util.sha256(
                    self.version +
                    hash_prev_outs +
                    hash_sequence +
                    self.TxIn[input_index].tx_id +
                    self.TxIn[input_index].tx_index +
                    # scriptCode length
                    self.TxIn[input_index].script_sig_len +
                    # scriptCode (includes amount)
                    self.TxIn[input_index].script_sig +
                    self.TxIn[input_index].sequence +
                    hash_outputs +
                    self.lock_time +
                    hash_type
                )
            else:
                hashed = util.sha256(
                    self.version +
                    input_count +
                    b''.join(
                        ti.tx_id + ti.tx_index + constants.OP_0 + ti.sequence
                        for ti in itertools.islice(self.TxIn, input_index)
                    ) +
                    self.TxIn[input_index].tx_id +
                    self.TxIn[input_index].tx_index +
                    # scriptCode length
                    self.TxIn[input_index].script_sig_len +
                    self.TxIn[input_index].script_sig +  # scriptCode
                    self.TxIn[input_index].sequence +
                    b''.join(
                        ti.tx_id + ti.tx_index + constants.OP_0 + ti.sequence
                        for ti in itertools.islice(
                            self.TxIn,
                            input_index + 1,
                            None)
                    ) +
                    output_count +
                    output_block +
                    self.lock_time +
                    hash_type
                )
            preimages.append(hashed)
        return preimages


def estimate_tx_size(in_size: int, n_in: int, out_size: int, n_out: int) -> int:
    return (
        in_size
        + len(util.number_to_unknown_bytes(n_in, byteorder='little'))
        + out_size
        + len(util.number_to_unknown_bytes(n_out, byteorder='little'))
        + 8
    )


def construct_outputs(outputs: List[Tuple[str, int]]) -> List[TxOutput]:
    outputs_obj = []

    for address_name, amount in outputs:
        log.debug(f"destination: {address_name} amount: {amount}")

        # P2PKH/P2SH/Bech32
        if True:
            script_pubkey = util.address_to_scriptpubkey(address_name)
            amount = int(amount).to_bytes(8, byteorder='little')

        # TODO Blockchain storage
        """
        else:
            from .constants import OP_RETURN
            script_pubkey = (OP_RETURN +
                             len(address_name).to_bytes(1, byteorder='little') +
                             address_name)

            amount = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        """

        assert address_name
        outputs_obj.append(TxOutput(
            amount,
            script_pubkey,
            address=address_name))

    return outputs_obj
