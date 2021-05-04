"""
https://en.bitcoin.it/wiki/Protocol_documentation
"""
from __future__ import annotations

import itertools
import logging
import random
import re
from collections import namedtuple
from typing import Union, List, Tuple
from ..coins.tx import AbstractUtxo

from . import constants, util

log = logging.getLogger(__name__)

TX_TRUST_LOW = 1
TX_TRUST_MEDIUM = 6
TX_TRUST_HIGH = 30


class InsufficientFunds(Exception):
    pass


UNSPENT_TYPES = {
    # Dictionary containing as keys known unspent types and as value a
    # dictionary containing information if spending uses a witness
    # program (Segwit) and its estimated scriptSig size.
    'unknown': {'segwit': None, 'vsize': 180},     # Unknown type
    'p2pkh-uncompressed':                          # Legacy P2PKH using
               {'segwit': False, 'vsize': 180},    # uncompressed keys
    'p2pkh':   {'segwit': False, 'vsize': 148},    # Legacy P2PKH
    # Legacy P2SH (vsize corresponds to a 2-of-3 multisig input)
    'p2sh':    {'segwit': False, 'vsize': 292},
    'np2wkh':  {'segwit': True,  'vsize': 90},     # (Nested) P2SH-P2WKH
    # (Nested) P2SH-P2WSH (vsize corresponds to a 2-of-3 multisig input)
    'np2wsh':  {'segwit': True,  'vsize': 139},
    # Bech32 P2WKH -- Not yet supported to sign
    'p2wpkh':   {'segwit': True,  'vsize': 67},
    # Bech32 P2WSH -- Not yet supported to sign (vsize corresponds to a 2-of-3 multisig input)
    'p2wsh':   {'segwit': True,  'vsize': 104}
}


class UTXO(AbstractUtxo):
    def __init__(
            self,
            address,
            *,
            script = None,
            type='p2pkh',
            vsize=None,
            **kwargs) -> None:
        super().__init__(address, **kwargs)

        self.script = script
        self.type = type if type in UNSPENT_TYPES else 'unknown'
        assert 'unknown' != self.type
        self.vsize = vsize if vsize else UNSPENT_TYPES[self.type]['vsize']
        self.segwit = UNSPENT_TYPES[self.type]['segwit']

    def __hash__(self) -> int:
        return hash((self.amount, self.address, self.script, self.txName, self.index))

    def __eq__(self, other) -> bool:
        return (self.amount == other.amount and
                self.address == other.address and
                self.script == other.script and
                self.txName == other.txName and
                self.index == other.index and
                self.segwit == other.segwit)

    def set_type(self, type, vsize=0):
        self.type = type if type in UNSPENT_TYPES else 'unknown'
        self.vsize = vsize if vsize else UNSPENT_TYPES[self.type]['vsize']
        self.segwit = UNSPENT_TYPES[self.type]['segwit']
        return self


class TxEntity:
    def __init__(self, address: str):
        self._address = address
        self.amount = None

    @property
    def amount_int(self):
        if isinstance(self.amount, bytes):
            return int.from_bytes(self.amount, "little")
        return self.amount

    @property
    def address(self) -> str:
        return self._address

    def __eq__(self, other: 'TxEntity'):
        return isinstance(other, self.__class__) and self._address == other._address


class TxInput(TxEntity):
    __slots__ = ('script_sig', 'script_sig_len', 'txid', 'txindex', 'witness',
                 'amount', 'sequence', 'segwit_input')

    def __init__(
            self,
            script_sig,
            txid,
            txindex,
            witness=b'',
            amount=None,
            sequence=constants.SEQUENCE,
            segwit_input=False,
            address: str = None):
        super().__init__(address)

        self.script_sig = script_sig
        self.script_sig_len = util.int_to_varint(len(script_sig))
        self.txid = txid
        self.txindex = txindex
        self.witness = witness
        self.amount = amount
        self.sequence = sequence
        self.segwit_input = segwit_input

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return (self.script_sig == other.script_sig and
                self.script_sig_len == other.script_sig_len and
                self.txid == other.txid and
                self.txindex == other.txindex and
                self.witness == other.witness and
                self.amount == other.amount and
                self.sequence == other.sequence and
                self.segwit_input == other.segwit_input)

    def __repr__(self):
        if self.is_segwit():
            return f"TxInput<{self._address}>[{self.script_sig}, {self.script_sig_len}, {self.txid}, {self.txindex}, {self.witness}, {self.amount}, {self.sequence}]"
        return f"TxInput<{self._address}>[{self.script_sig}, {self.script_sig_len}, {self.txid}, {self.txindex}, {self.sequence}]"

    def __bytes__(self):
        return b''.join([
            self.txid,
            self.txindex,
            self.script_sig_len,
            self.script_sig,
            self.sequence
        ])

    def is_segwit(self):
        return self.segwit_input or self.witness


Output = namedtuple('Output', ('address', 'amount', 'currency'))


class TxOutput(TxEntity):
    __slots__ = ('amount', 'script_pubkey_len', 'script_pubkey')

    def __init__(self, amount, script_pubkey, address: str = None):
        super().__init__(address)
        self.amount = amount
        self.script_pubkey = script_pubkey
        self.script_pubkey_len = util.int_to_varint(len(script_pubkey))

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return (self.amount == other.amount and
                self.script_pubkey == other.script_pubkey and
                self.script_pubkey_len == other.script_pubkey_len)

    def __repr__(self):
        return f"TxOut<{self._address}>({self.amount}, {self.script_pubkey}, {self.script_pubkey_len})"

    def __bytes__(self):
        return b''.join([
            self.amount,
            self.script_pubkey_len,
            self.script_pubkey
        ])


class MtxError(Exception):
    pass


class NoInputsToSignError(MtxError):
    pass


class Mtx:
    def __init__(self, version, TxIn, TxOut, locktime) -> None:
        segwit_tx = any([i.segwit_input or i.witness for i in TxIn])
        self.version = version
        self.TxIn = TxIn
        if segwit_tx:
            for i in self.TxIn:
                i.witness = i.witness if i.witness else b'\x00'
        self.TxOut = TxOut
        self.locktime = locktime

    def __eq__(self, other):
        return (self.version == other.version and
                self.TxIn == other.TxIn and
                self.TxOut == other.TxOut and
                self.locktime == other.locktime)

    def __repr__(self):
        return f"Mtx({self.version}, {self.TxIn}, {self.TxOut}, {self.locktime})"

    def __bytes__(self):
        inp = util.int_to_varint(len(self.TxIn)) + \
            b''.join(map(bytes, self.TxIn))
        out = util.int_to_varint(len(self.TxOut)) + \
            b''.join(map(bytes, self.TxOut))
        wit = b''.join([w.witness for w in self.TxIn])
        return b''.join([
            self.version,
            constants.WIT_MARKER if wit else b'',
            constants.WIT_FLAG if wit else b'',
            inp,
            out,
            wit,
            self.locktime
        ])

    def __hash__(self):
        return hash(self.to_hex())

    def legacy_repr(self):
        inp = util.int_to_varint(len(self.TxIn)) + \
            b''.join(map(bytes, self.TxIn))
        out = util.int_to_varint(len(self.TxOut)) + \
            b''.join(map(bytes, self.TxOut))
        return b''.join([
            self.version,
            inp,
            out,
            self.locktime
        ])

    def to_hex(self):
        return util.bytes_to_hex(bytes(self))

    @classmethod
    def make(cls, utxo_list: List[UTXO], outputs: List[Tuple[str, int]]):
        version = constants.VERSION_1
        lock_time = constants.LOCK_TIME
        outputs = construct_outputs(outputs)

        # Optimize for speed, not memory, by pre-computing values.
        inputs = []
        for unspent in utxo_list:
            script_sig = b''  # empty scriptSig for new unsigned transaction.
            txid = util.hex_to_bytes(unspent.txName)[::-1]
            txindex = unspent.index.to_bytes(4, byteorder='little')
            amount = int(unspent.amount).to_bytes(8, byteorder='little')
            assert unspent.address
            inputs.append(
                TxInput(
                    script_sig,
                    txid,
                    txindex,
                    amount=amount,
                    segwit_input=unspent.segwit,
                    address=unspent.address.name))
        out = cls(version, inputs, outputs, lock_time)
        out.unspents = utxo_list
        return out

    @property
    def in_amount(self):
        return sum(inc.amount_int for inc in self.TxIn)

    @property
    def out_amount(self):
        return sum(out.amount_int for out in self.TxOut)

    @property
    def feeAmount(self) -> int:
        return self.in_amount - self.out_amount

    @classmethod
    def is_segwit(cls, tx):
        if isinstance(tx, cls):
            tx = bytes(tx)
        elif not isinstance(tx, bytes):
            tx = util.hex_to_bytes(tx)
        # log.debug(f"segwit test: {tx[4:6]} {constants.WIT_MARKER + constants.WIT_FLAG}")
        return tx[4:6] == constants.WIT_MARKER + constants.WIT_FLAG

    @property
    def id(self) -> str:
        return util.bytes_to_hex(util.sha256d(self.legacy_repr())[::-1])

    @classmethod
    def calc_id(cls, data) -> str:
        return cls.parse(data).id

    @classmethod
    def parse(cls, tx: Union[str, bytes]) -> 'Mtx':
        if isinstance(tx, str) and re.match('^[0-9a-fA-F]*$', tx):
            return cls.parse(util.hex_to_bytes(tx))

        segwit_tx = Mtx.is_segwit(tx)

        version, tx = util.split_bytes(tx, 4)

        if segwit_tx:
            _, tx = util.split_bytes(tx, 1)  # ``marker`` is nulled
            _, tx = util.split_bytes(tx, 1)  # ``flag`` is nulled

        ins, tx = util.read_var_int(tx)
        inputs = []
        for i in range(ins):
            txid, tx = util.split_bytes(tx, 32)
            txindex, tx = util.split_bytes(tx, 4)
            script_sig, tx = util.read_var_string(tx)
            sequence, tx = util.split_bytes(tx, 4)
            inputs.append(TxInput(script_sig, txid,
                                  txindex, sequence=sequence))

        outs, tx = util.read_var_int(tx)
        outputs = []
        for _ in range(outs):
            amount, tx = util.split_bytes(tx, 8)
            script_pubkey, tx = util.read_var_string(tx)
            outputs.append(TxOutput(amount, script_pubkey))

        if segwit_tx:
            for i in range(ins):
                wnum, tx = util.read_var_int(tx)
                witness = util.int_to_varint(wnum)
                for _ in range(wnum):
                    w, tx = util.read_segwit_string(tx)
                    witness += w
                inputs[i].witness = witness

        locktime, _ = util.split_bytes(tx, 4)

        return cls(version, inputs, outputs, locktime)

    def sign(self, private_key, *, utxo_list: list = None) -> str:
        input_dict = {}
        try:
            for unspent in (utxo_list or self.unspents):
                if not private_key.can_sign_unspent(unspent):
                    log.warning(f"key {private_key} can't sign {unspent}")
                    continue
                tx_input = \
                    util.hex_to_bytes(unspent.txName)[::-1] \
                    + unspent.index.to_bytes(4, byteorder='little')
                input_dict[tx_input] = unspent.serialize()
                input_dict[tx_input]["segwit"] = unspent.segwit  # TODO tmp
        except TypeError:
            raise TypeError('Please provide as unspents at least all inputs to '
                            'be signed with the function call in a list.')
        # Determine input indices to sign from input_dict (allows for transaction batching)
        sign_inputs = [j for j, i in enumerate(self.TxIn) if i.txid + i.txindex in input_dict]

        segwit_tx = Mtx.is_segwit(self)
        public_key = private_key.public_key
        public_key_push = util.script_push(len(public_key))
        hash_type = constants.HASH_TYPE
        inputs_parameters = []
        input_script_field = [
            self.TxIn[i].script_sig for i in range(len(self.TxIn))]
        if not sign_inputs:
            raise NoInputsToSignError()
        for i in sign_inputs:
            tx_in = self.TxIn[i]
            # Create transaction object for preimage calculation
            tx_input = tx_in.txid + tx_in.txindex
            segwit_input = input_dict[tx_input]['segwit']
            tx_in.segwit_input = segwit_input

            script_code = private_key.scriptcode
            script_code_len = util.int_to_varint(len(script_code))

            # Use scriptCode for preimage calculation of transaction object:
            tx_in.script_sig = script_code
            tx_in.script_sig_len = script_code_len

            if segwit_input:
                try:
                    tx_in.script_sig += input_dict[tx_input]['amount']\
                        .to_bytes(8, byteorder='little')

                    # For partially signed Segwit transactions the signatures must
                    # be extracted from the witnessScript field:
                    input_script_field[i] = tx_in.witness
                except AttributeError:
                    raise ValueError(
                        'Cannot sign a segwit input when the input\'s amount is '
                        'unknown. Maybe no network connection or the input is '
                        'already spent? Then please provide all inputs to sign as '
                        '`UTXO` objects to the function call.')

            inputs_parameters.append([i, hash_type, segwit_input])

        preimages = self.calc_preimages(inputs_parameters)

        for hash_, (i, _, segwit_input) in zip(preimages, inputs_parameters):
            tx_in = self.TxIn[i]
            signature = private_key.sign(hash_) + b'\x01'
            if private_key.is_multi_sig:
                raise NotImplementedError("Multisig will be implemented later")
            else:
                script_sig = b'\x16' + private_key.segwit_scriptcode

                witness = (
                    (b'\x02' if segwit_input else b'') +  # witness counter
                    len(signature).to_bytes(1, byteorder='little') +
                    signature +
                    public_key_push +
                    public_key.data
                )

                # script_sig = script_sig if segwit_input else witness
                script_sig = b'' if segwit_input else witness
                witness = witness if segwit_input else (
                    b'\x00' if segwit_tx else b'')

            # Providing the signature(s) to the input
            tx_in.script_sig = script_sig
            tx_in.script_sig_len = util.int_to_varint(len(script_sig))
            tx_in.witness = witness
        return self.to_hex()

    def calc_preimages(self, inputs_parameters):

        input_count = util.int_to_varint(len(self.TxIn))
        output_count = util.int_to_varint(len(self.TxOut))
        output_block = b''.join([bytes(o) for o in self.TxOut])

        hashPrevouts = util.sha256d(
            b''.join([i.txid+i.txindex for i in self.TxIn]))
        hashSequence = util.sha256d(
            b''.join([i.sequence for i in self.TxIn]))
        hashOutputs = util.sha256d(output_block)

        preimages = []
        for input_index, hash_type, segwit_input in inputs_parameters:
            # We can only handle hashType == 1:
            if hash_type != constants.HASH_TYPE:
                raise ValueError('Bit only support hashType of value 1.')
            # Calculate prehashes:
            if segwit_input:
                # BIP-143 preimage:
                hashed = util.sha256(
                    self.version +
                    hashPrevouts +
                    hashSequence +
                    self.TxIn[input_index].txid +
                    self.TxIn[input_index].txindex +
                    # scriptCode length
                    self.TxIn[input_index].script_sig_len +
                    # scriptCode (includes amount)
                    self.TxIn[input_index].script_sig +
                    self.TxIn[input_index].sequence +
                    hashOutputs +
                    self.locktime +
                    hash_type
                )
            else:
                hashed = util.sha256(
                    self.version +
                    input_count +
                    b''.join(ti.txid + ti.txindex + constants.OP_0 + ti.sequence
                             for ti in itertools.islice(self.TxIn, input_index)) +
                    self.TxIn[input_index].txid +
                    self.TxIn[input_index].txindex +
                    # scriptCode length
                    self.TxIn[input_index].script_sig_len +
                    self.TxIn[input_index].script_sig +  # scriptCode
                    self.TxIn[input_index].sequence +
                    b''.join(ti.txid + ti.txindex + constants.OP_0 + ti.sequence
                             for ti in itertools.islice(self.TxIn, input_index + 1, None)) +
                    output_count +
                    output_block +
                    self.locktime +
                    hash_type
                )
            preimages.append(hashed)
        return preimages


def estimate_tx_size(in_size, n_in, out_size, n_out):
    return (
        in_size
        + len(util.number_to_unknown_bytes(n_in, byteorder='little'))
        + out_size
        + len(util.number_to_unknown_bytes(n_out, byteorder='little'))
        + 8
    )


def estimate_tx_fee(in_size, n_in, out_size, n_out, satoshis):
    if not satoshis:
        return 0
    return estimate_tx_size(in_size, n_in, out_size, n_out) * satoshis


def select_coins(target, fee_amount, output_size, min_change, *, absolute_fee=False,
                 consolidate=False, utxo_list):
    BNB_TRIES = 1000000
    COST_OF_OVERHEAD = (8 + sum(output_size[:-1]) + 1) * fee_amount

    def branch_and_bound(d, selected_coins, effective_value, target, fee_amount,
                         sorted_utxo_list):  # pragma: no cover

        nonlocal COST_OF_OVERHEAD, BNB_TRIES
        BNB_TRIES -= 1
        COST_PER_INPUT = 148 * fee_amount  # Just typical estimate values
        COST_PER_OUTPUT = 34 * fee_amount
        target_to_match = target + COST_OF_OVERHEAD
        match_range = COST_PER_INPUT + COST_PER_OUTPUT
        if effective_value > target_to_match + match_range:
            return []
        elif effective_value >= target_to_match:
            return selected_coins
        elif BNB_TRIES <= 0:
            return []
        elif d >= len(sorted_utxo_list):
            return []
        else:
            binary_random = random.randint(0, 1)
            if binary_random:
                effective_value_new = effective_value + \
                    sorted_utxo_list[d].amount - fee_amount * sorted_utxo_list[d].vsize

                with_this = branch_and_bound(
                    d + 1,
                    selected_coins + [sorted_utxo_list[d]],
                    effective_value_new,
                    target,
                    fee_amount,
                    sorted_utxo_list
                )

                if with_this != []:
                    return with_this
                else:
                    without_this = branch_and_bound(
                        d + 1,
                        selected_coins,
                        effective_value,
                        target,
                        fee_amount,
                        sorted_utxo_list
                    )

                    return without_this

            else:
                without_this = branch_and_bound(
                    d + 1,
                    selected_coins,
                    effective_value,
                    target,
                    fee_amount,
                    sorted_utxo_list
                )

                if without_this != []:
                    return without_this
                else:
                    effective_value_new = effective_value + \
                        sorted_utxo_list[d].amount - \
                        fee_amount * sorted_utxo_list[d].vsize

                    with_this = branch_and_bound(
                        d + 1,
                        selected_coins + [sorted_utxo_list[d]],
                        effective_value_new,
                        target,
                        fee_amount,
                        sorted_utxo_list
                    )

                    return with_this

    sorted_utxo_list = sorted(utxo_list, key=lambda u: u.amount, reverse=True)
    selected_coins = []

    if not consolidate:
        selected_coins = branch_and_bound(
            d=0,
            selected_coins=[],
            effective_value=0,
            target=target,
            fee_amount=fee_amount,
            sorted_utxo_list=sorted_utxo_list
        )
        remaining = 0

    if selected_coins == []:
        utxo_list = utxo_list.copy()
        if not consolidate:
            random.shuffle(utxo_list)
        while utxo_list:
            selected_coins.append(utxo_list.pop(0))
            estimated_fee = estimate_tx_fee(
                sum(u.vsize for u in selected_coins),
                len(selected_coins),
                sum(output_size),
                len(output_size),
                fee_amount
            )
            estimated_fee = fee_amount if absolute_fee else estimated_fee
            remaining = sum(u.amount for u in selected_coins) - \
                target - estimated_fee
            if remaining >= min_change and (not consolidate or len(utxo_list) == 0):
                break
        else:
            raise InsufficientFunds(
                'Balance {} is less than {} (including fee).'
                .format(
                    sum(u.amount for u in selected_coins),
                    target + min_change + estimated_fee))

    return selected_coins, remaining


def deserialize(data):
    return Mtx.parse(data)


def sanitize_tx_data(utxo_list, outputs, fee_amount, leftover, combine=True,
                     message=None, compressed=True, absolute_fee=False,
                     min_change=0, version='main', message_is_hex=False):
    """
    sanitize_tx_data()

    fee is in satoshis per byte.
    """

    outputs = outputs.copy()

    for i, output in enumerate(outputs):
        dest, amount, currency = output
        outputs[i] = (dest, amount)
        # outputs[i] = (dest, rates.currency_to_satoshi_cached(amount, currency))

    if not utxo_list:
        raise ValueError('Transactions must have at least one unspent.')

    # Temporary storage so all outputs precede messages.
    messages = []

    if message:
        if message_is_hex:
            message_chunks = util.chunk_data(message, constants.MESSAGE_LIMIT)
        else:
            message_chunks = util.chunk_data(
                message.encode('utf-8'), constants.MESSAGE_LIMIT)

        for message in message_chunks:
            messages.append((message, 0))

    output_size = [len(util.address_to_scriptpubkey(o[0])) +
                   9 for o in outputs]
    output_size.append(len(messages) * (constants.MESSAGE_LIMIT + 9))
    output_size.append(len(util.address_to_scriptpubkey(leftover)) + 9)
    sum_outputs = sum(out[1] for out in outputs)

    utxo_list[:], remaining = select_coins(
        sum_outputs, fee_amount, output_size, min_change=min_change,
        absolute_fee=absolute_fee, consolidate=combine, utxo_list=utxo_list
    )

    if remaining > 0:
        outputs.append((leftover, remaining))
    for output in outputs:
        dest, amount = output
        vs = util.get_version(dest)
        if vs and vs != version:
            raise ValueError(
                f"Cannot send to {vs}net address when spending from a {version}net address.")

    outputs.extend(messages)

    return utxo_list, outputs


def construct_outputs(outputs):
    outputs_obj = []

    for dest, amount in outputs:
        log.debug(f"dest:{dest} amount:{amount}")

        # P2PKH/P2SH/Bech32
        if True:
            script_pubkey = util.address_to_scriptpubkey(dest)

            amount = int(amount).to_bytes(8, byteorder='little')

        # TODO Blockchain storage
        else:
            from .constants import OP_RETURN
            script_pubkey = (OP_RETURN +
                             len(dest).to_bytes(1, byteorder='little') +
                             dest)

            amount = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        assert dest
        outputs_obj.append(TxOutput(amount, script_pubkey, address=dest))

    return outputs_obj


def calculate_preimages(mtx, inputs_parameters):
    return mtx.calc_preimages(inputs_parameters)


def calc_txid(tx_hex):
    return Mtx.calc_id(tx_hex)


def sign_tx(private_key, tx, *, utxo_list: list) -> str:
    return tx.sign(private_key, utxo_list=utxo_list)


def create_new_transaction(private_key, utxo_list, outputs) -> str:
    return Mtx.make(utxo_list, outputs).sign(private_key, utxo_list=utxo_list)
