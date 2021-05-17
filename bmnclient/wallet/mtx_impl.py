from __future__ import annotations

import itertools
import logging
from typing import TYPE_CHECKING

from . import constants
from ..crypto.digest import Sha256Digest, Sha256DoubleDigest

if TYPE_CHECKING:
    from typing import List, Tuple
    from ..coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class TxEntity:
    def __init__(
            self,
            address: AbstractCoin.Address,
            amount: bytes) -> None:
        self._address = address
        self._amount = amount

    @property
    def amount(self) -> bytes:
        return self._amount

    @property
    def amount_int(self) -> int:
        return self._address.coin.Script.integerFromBytes(self._amount)

    @property
    def address(self) -> AbstractCoin.Address:
        return self._address

    def __eq__(self, other: TxEntity):
        return (
                isinstance(other, self.__class__)
                and self._address == other._address
        )


class TxInput(TxEntity):
    def __init__(
            self,
            *,
            address: AbstractCoin.Address,
            amount: bytes,
            script_sig: bytes,
            tx_id: bytes,
            tx_index: bytes,
            witness: bytes = b"",
            sequence: bytes = constants.SEQUENCE,
            segwit_input: bool) -> None:
        super().__init__(address, amount)
        self._script_sig = script_sig
        self._script_sig_len = self._address.coin.Script.integerToVarInt(
            len(script_sig))
        self._tx_id = tx_id
        self._tx_index = tx_index
        self._witness = witness
        self._sequence = sequence
        self._segwit_input = segwit_input

    def __eq__(self, other: TxInput):
        if not super().__eq__(other):
            return False
        return (self._script_sig == other._script_sig and
                self._script_sig_len == other._script_sig_len and
                self._tx_id == other._tx_id and
                self._tx_index == other._tx_index and
                self._witness == other._witness and
                self._amount == other._amount and
                self._sequence == other._sequence and
                self._segwit_input == other._segwit_input)

    def __bytes__(self) -> bytes:
        return b''.join([
            self._tx_id,
            self._tx_index,
            self._script_sig_len,
            self._script_sig,
            self._sequence
        ])

    @property
    def script_sig(self) -> bytes:
        return self._script_sig

    @script_sig.setter
    def script_sig(self, value: bytes) -> None:
        self._script_sig = value

    @property
    def script_sig_len(self) -> bytes:
        return self._script_sig_len

    @script_sig_len.setter
    def script_sig_len(self, value: bytes) -> None:
        self._script_sig_len = value

    @property
    def tx_id(self) -> bytes:
        return self._tx_id

    @property
    def tx_index(self) -> bytes:
        return self._tx_index

    @property
    def is_segwit(self) -> bool:
        return self._segwit_input or self._witness

    @property
    def witness(self) -> bytes:
        return self._witness

    @witness.setter
    def witness(self, value: bytes) -> None:
        self._witness = value

    @property
    def sequence(self) -> bytes:
        return self._sequence


class TxOutput(TxEntity):
    def __init__(
            self,
            *,
            address: AbstractCoin.Address,
            amount: bytes,
            script: bytes) -> None:
        super().__init__(address, amount)
        self._script = script
        self._script_len = self._address.coin.Script.integerToVarInt(
            len(self._script))

    def __eq__(self, other: TxOutput):
        if not super().__eq__(other):
            return False
        return (self._amount == other._amount and
                self._script == other._script and
                self._script_len == other._script_len)

    def __bytes__(self) -> bytes:
        return b''.join([
            self._amount,
            self._script_len,
            self._script
        ])


class NoInputsToSignError(Exception):
    pass


class Mtx:
    def __init__(
            self,
            *,
            coin: AbstractCoin,
            version: bytes,
            utxo_list: List[AbstractCoin.Tx.Utxo],
            tx_in: List[TxInput],
            tx_out: List[TxOutput],
            lock_time: bytes) -> None:
        self._coin = coin
        self._version = version
        self._utxo_list = utxo_list
        self._tx_in = tx_in
        self._tx_out = tx_out
        self._lock_time = lock_time

        if any([i.is_segwit for i in tx_in]):
            for i in self._tx_in:
                if not i.witness:
                    i.witness = b"\x00"

    def __bytes__(self) -> bytes:
        input_list = \
            self._coin.Script.integerToVarInt(len(self._tx_in)) \
            + b"".join(map(lambda v: v.__bytes__(), self._tx_in))

        output_list = \
            self._coin.Script.integerToVarInt(len(self._tx_out)) \
            + b"".join(map(lambda v: v.__bytes__(), self._tx_out))

        witness_list = b"".join([w.witness for w in self._tx_in])

        return b''.join([
            self._version,
            constants.WIT_MARKER if witness_list else b"",
            constants.WIT_FLAG if witness_list else b"",
            input_list,
            output_list,
            witness_list,
            self._lock_time
        ])

    def __eq__(self, other: Mtx) -> bool:
        return (
                self._version == other._version
                and self._tx_in == other._tx_in
                and self._tx_out == other._tx_out
                and self._lock_time == other._lock_time
        )

    def __hash__(self) -> int:
        return hash((bytes(self), ))

    @property
    def coin(self) -> AbstractCoin:
        return self._coin

    def legacy_repr(self) -> bytes:
        input_list = \
            self._coin.Script.integerToVarInt(len(self._tx_in)) \
            + b"".join(map(lambda v: v.__bytes__(), self._tx_in))

        output_list = \
            self._coin.Script.integerToVarInt(len(self._tx_out)) \
            + b"".join(map(lambda v: v.__bytes__(), self._tx_out))

        return b''.join([
            self._version,
            input_list,
            output_list,
            self._lock_time
        ])

    @classmethod
    def make(
            cls,
            coin: AbstractCoin,
            utxo_list: List[AbstractCoin.Tx.Utxo],
            output_list: List[Tuple[AbstractCoin.Address, int]]):
        tx_out = []
        for address, amount in output_list:
            log.debug(f"destination: {address.name} amount: {amount}")
            tx_out.append(TxOutput(
                address=address,
                amount=int(amount).to_bytes(8, byteorder='little'),
                script=coin.Script.addressToScript(address)))

        tx_in = []
        for utxo in utxo_list:
            tx_in.append(TxInput(
                address=utxo.address,
                amount=int(utxo.amount).to_bytes(8, byteorder='little'),
                script_sig=b"",  # empty scriptSig for new unsigned transaction.
                tx_id=bytes.fromhex(utxo.name)[::-1],
                tx_index=utxo.index.to_bytes(4, byteorder='little'),
                segwit_input=utxo.segwit))

        return cls(
            coin=coin,
            version=constants.VERSION_1,
            utxo_list=utxo_list,
            tx_in=tx_in,
            tx_out=tx_out,
            lock_time=constants.LOCK_TIME)

    @property
    def feeAmount(self) -> int:
        i = sum(i.amount_int for i in self._tx_in)
        o = sum(o.amount_int for o in self._tx_out)
        return i - o

    @property
    def is_segwit(self) -> bool:
        return bytes(self)[4:6] == (constants.WIT_MARKER + constants.WIT_FLAG)

    @property
    def id(self) -> str:
        return Sha256DoubleDigest(self.legacy_repr()).finalize()[::-1].hex()

    def sign(
            self,
            address: AbstractCoin.Address,
            *,
            utxo_list: List[AbstractCoin.Tx.Utxo]) -> str:
        input_dict = {}
        try:
            for utxo in utxo_list:
                tx_input = \
                    bytes.fromhex(utxo.name)[::-1] \
                    + utxo.index.to_bytes(4, byteorder='little')
                input_dict[tx_input] = utxo.serialize()
                input_dict[tx_input]["segwit"] = utxo.segwit  # TODO tmp
        except TypeError:
            raise TypeError('please provide as unspent at least all inputs to '
                            'be signed with the function call in a list')
        # Determine input indices to sign from input_dict (allows for
        # transaction batching)
        sign_inputs = [
            j for j, i in enumerate(self._tx_in)
            if (i.tx_id + i.tx_index) in input_dict
        ]

        segwit_tx = self.is_segwit
        public_key_push = script_push(len(address.publicKey.data))
        inputs_parameters = []
        input_script_field = [
            self._tx_in[i].script_sig for i in range(len(self._tx_in))]
        if not sign_inputs:
            raise NoInputsToSignError()
        for i in sign_inputs:
            tx_in = self._tx_in[i]
            # Create transaction object for preimage calculation
            tx_input = tx_in.tx_id + tx_in.tx_index
            segwit_input = input_dict[tx_input]["segwit"]
            tx_in.segwit_input = segwit_input

            # Use scriptCode for preimage calculation of transaction object:
            tx_in.script_sig = self._coin.Script.addressToScript(
                address,
                address.Type.PUBKEY_HASH)  # TODO SCRIPT_HASH?
            tx_in.script_sig_len = self._coin.Script.integerToVarInt(
                len(tx_in.script_sig))

            if segwit_input:
                try:
                    tx_in.script_sig += input_dict[tx_input]["amount"] \
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

            inputs_parameters.append((i, constants.HASH_TYPE, segwit_input))

        preimages = self.calc_preimages(inputs_parameters)

        for hash_, (i, _, segwit_input) in zip(preimages, inputs_parameters):
            tx_in = self._tx_in[i]
            signature = address.privateKey.sign(hash_) + b'\x01'
            if True:
                witness = (
                    (b'\x02' if segwit_input else b'') +  # witness counter
                    len(signature).to_bytes(1, byteorder='little') +
                    signature +
                    public_key_push +
                    address.publicKey.data
                )

                script_sig = b'' if segwit_input else witness
                witness = witness if segwit_input else (
                    b'\x00' if segwit_tx else b'')

            # Providing the signature(s) to the input
            tx_in.script_sig = script_sig
            tx_in.script_sig_len = self._coin.Script.integerToVarInt(
                len(script_sig))
            tx_in.witness = witness
        return bytes(self).hex()

    def calc_preimages(
            self,
            inputs_parameters: List[Tuple[int, bytes, bool]]) \
            -> List[bytes]:
        input_count = self._coin.Script.integerToVarInt(len(self._tx_in))
        output_count = self._coin.Script.integerToVarInt(len(self._tx_out))
        output_block = b"".join([bytes(o) for o in self._tx_out])

        hash_prev_outs = Sha256DoubleDigest(
            b"".join([i.tx_id + i.tx_index for i in self._tx_in])).finalize()
        hash_sequence = Sha256DoubleDigest(
            b"".join([i.sequence for i in self._tx_in])).finalize()
        hash_outputs = Sha256DoubleDigest(output_block).finalize()

        preimages = []
        for input_index, hash_type, segwit_input in inputs_parameters:
            # We can only handle hashType == 1:
            if hash_type != constants.HASH_TYPE:
                raise ValueError('bit only support hashType of value 1')

            # Calculate pre hashes:
            if segwit_input:
                # BIP-143 preimage:
                hashed = Sha256Digest(
                    self._version +
                    hash_prev_outs +
                    hash_sequence +
                    self._tx_in[input_index].tx_id +
                    self._tx_in[input_index].tx_index +
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
                        ti.tx_id + ti.tx_index + constants.OP_0 + ti.sequence
                        for ti in itertools.islice(self._tx_in, input_index)
                    ) +
                    self._tx_in[input_index].tx_id +
                    self._tx_in[input_index].tx_index +
                    # scriptCode length
                    self._tx_in[input_index].script_sig_len +
                    self._tx_in[input_index].script_sig +  # scriptCode
                    self._tx_in[input_index].sequence +
                    b"".join(
                        ti.tx_id + ti.tx_index + constants.OP_0 + ti.sequence
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


def estimate_tx_size(in_size: int, n_in: int, out_size: int, n_out: int) -> int:
    return (
        in_size
        + len(number_to_unknown_bytes(n_in, byteorder='little'))
        + out_size
        + len(number_to_unknown_bytes(n_out, byteorder='little'))
        + 8
    )


def number_to_unknown_bytes(num: int, byteorder: str = 'big') -> bytes:
    """Converts an int to the least number of bytes as possible."""
    return num.to_bytes((num.bit_length() + 7) // 8 or 1, byteorder)


def script_push(val: int) -> bytes:
    if val <= 75:
        return number_to_unknown_bytes(val)
    elif val < 256:
        return b'\x4c'+number_to_unknown_bytes(val)
    elif val < 65536:
        return b'\x4d'+val.to_bytes(2, 'little')
    else:
        return b'\x4e'+val.to_bytes(4, 'little')
