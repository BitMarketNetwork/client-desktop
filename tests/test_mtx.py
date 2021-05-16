
import copy
import json
import logging
from typing import List, Tuple
import unittest
from tests import TEST_DATA_PATH
from tests.test_data import *
from unittest import skip

from bmnclient.wallet import constants
from bmnclient.wallet import mtx_impl as mtx
from bmnclient.wallet import util

log = logging.getLogger(__name__)

"""
OUTPUTS = [
    ('n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi', 50000),
    ('mtrNwJxS1VyHYn3qBY1Qfsm3K3kh1mGRMS', 83658760)
]
UNSIGNED_TX_SEGWIT = (
    '0100000000010288d3b28dbb7d24dd4ff292534dec44bdb9eca73c3c9577e4d7fc70777122'
    '9cf00000000000ffffffffcbd4b41660d8d348c15fc430deb5fd55d62cb756b36d1c5b9f3c'
    '5af9e14e2cf40000000000ffffffff0280f0fa020000000017a914ea654a94b18eb41ce290'
    'c135cccf9f348e7856a28770aaf0080000000017a9146015d175e191e6e5b99211e3ffc6ea'
    '7658cb051a87000000000000'
)
FINAL_TX_SEGWIT = ('0100000000010288d3b28dbb7d24dd4ff292534dec44bdb9eca73c3c95'
                   '77e4d7fc707771229cf0000000006b4830450221008dd5c2feb30d40dd'
                   '621afef413d3abc285d39aa0716233d7ccbc56a50678ebc4022005be97'
                   'c4e432d373885b20ae822c432f96f78ad290a191f060730997ade095b0'
                   '0121021816325d19fd34fd87a039e83e35fc9de3c9de64a501a6684b9b'
                   'f9946364fbb7ffffffffcbd4b41660d8d348c15fc430deb5fd55d62cb7'
                   '56b36d1c5b9f3c5af9e14e2cf40000000017160014905aa72f3d174709'
                   '4a24d3adbc38905bb451ffc8ffffffff0280f0fa020000000017a914ea'
                   '654a94b18eb41ce290c135cccf9f348e7856a28770aaf0080000000017'
                   'a9146015d175e191e6e5b99211e3ffc6ea7658cb051a87000247304402'
                   '2073604374fdbd121d8cf4facb19a553630d145e1a1405d8144d2c0cca'
                   '77da30ba022004a47a760b6bc68e99b88c1febfd8620d6bfd4f609b83e'
                   'e1c39f77f4689f69a20121021816325d19fd34fd87a039e83e35fc9de3'
                   'c9de64a501a6684b9bf9946364fbb700000000')
UNSPENTS_SEGWIT = [
    mtx.UTXO(100000000,
             1,
             '76a914905aa72f3d1747094a24d3adbc38905bb451ffc888ac',
             'f09c22717770fcd7e477953c3ca7ecb9bd44ec4d5392f24fdd247dbb8db2d388',
             0,
             'p2pkh'),
    mtx.UTXO(100000000,
             1,
             # 'a9146015d175e191e6e5b99211e3ffc6ea7658cb051a87', !!!
             '0014905aa72f3d1747094a24d3adbc38905bb451ffc8',
             'f42c4ee1f95a3c9f5b1c6db356b72cd655fdb5de30c45fc148d3d86016b4d4cb',
             0,
             'np2wkh')
]
UNSPENTS = [
    mtx.UTXO(83727960,
             15,
             '76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac',
             'f3ad23dac2a3546167b27a43ac3e370236caf93f75bfcf27c625ec839d397888',
             1)
]
"""

@unittest.skip
class TestInput(unittest.TestCase):

    def test_init(self):
        txin = mtx.TxInput(b'script', b'txid', b'\x04',
                           sequence=b'\xff\xff\xff\xff')
        self.assertEqual(txin.script_sig, b'script')
        self.assertEqual(txin.script_sig_len, b'\x06')
        self.assertEqual(txin.txid, b'txid')
        self.assertEqual(txin.txindex, b'\x04')
        self.assertEqual(txin.witness, b'')
        self.assertEqual(txin.sequence, b'\xff\xff\xff\xff')

    def test_init_segwit(self):
        txin = mtx.TxInput(b'script', b'txid', b'\x04',
                           b'witness', sequence=b'\xff\xff\xff\xff')
        self.assertEqual(txin.script_sig, b'script')
        self.assertEqual(txin.script_sig_len, b'\x06')
        self.assertEqual(txin.txid, b'txid')
        self.assertEqual(txin.txindex, b'\x04')
        self.assertEqual(txin.witness, b'witness')
        self.assertIsNone(txin.amount)
        self.assertEqual(txin.sequence, b'\xff\xff\xff\xff')

    def test_equality(self):
        txin1 = mtx.TxInput(b'script', b'txid', b'\x04',
                            sequence=b'\xff\xff\xff\xff')
        txin2 = mtx.TxInput(b'script', b'txid', b'\x04',
                            sequence=b'\xff\xff\xff\xff')
        txin3 = mtx.TxInput(b'script', b'txi', b'\x03',
                            sequence=b'\xff\xff\xff\xff')
        self.assertEqual(txin1, txin2)
        self.assertNotEqual(txin1, txin3)

    def test_bytes_repr(self):
        txin = mtx.TxInput(b'script', b'txid', b'\x04',
                           sequence=b'\xff\xff\xff\xff')
        self.assertEqual(bytes(txin), b''.join(
            [b'txid', b'\x04', b'\x06', b'script', b'\xff\xff\xff\xff']))


@unittest.skip
class TestOutput(unittest.TestCase):

    def test_init(self):
        txout = mtx.TxOutput(
            b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')
        self.assertEqual(txout.amount, b'\x88\x13\x00\x00\x00\x00\x00\x00')
        self.assertEqual(txout.script_pubkey_len, b'\r')
        self.assertEqual(txout.script_pubkey, b'script_pubkey')

    def test_equality(self):
        txout1 = mtx.TxOutput(
            b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')
        txout2 = mtx.TxOutput(
            b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')
        txout3 = mtx.TxOutput(
            b'\x88\x14\x00\x00\x00\x00\x00\x00', b'script_pubkey')
        txout4 = mtx.TxOutput(
            b'\x88\x14\x00\x00\x00\x00\x00\x00', b'script_pub')
        self.assertEqual(txout1, txout2)
        self.assertNotEqual(txout1, txout3)
        self.assertNotEqual(txout3, txout4)


@unittest.skip
class TestTransaction(unittest.TestCase):
    def test_init(self):
        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            sequence=b'\xff\xff\xff\xff')]
        txout = [
            mtx.TxOutput(b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        tx = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')
        self.assertEqual(tx.version,  b'\x01\x00\x00\x00')
        self.assertEqual(tx.locktime,  b'\x00\x00\x00\x00')

    def test_init_segwit(self):
        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            b'witness', sequence=b'\xff\xff\xff\xff')]
        txout = [
            mtx.TxOutput(b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        tx = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')
        self.assertEqual(tx.version,  b'\x01\x00\x00\x00')
        self.assertEqual(tx.locktime,  b'\x00\x00\x00\x00')

    def test_equality(self):
        txin1 = [mtx.TxInput(b'script', b'txid', b'\x04',
                             sequence=b'\xff\xff\xff\xff')]
        txin2 = [mtx.TxInput(b'scrip2', b'txid', b'\x04',
                             sequence=b'\xff\xff\xff\xff')]
        txout1 = [
            mtx.TxOutput(b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        txout2 = [
            mtx.TxOutput(b'\x88\x14\x00\x00\x00\x00\x00\x00', b'script_pubkey')]

        tx1 = mtx.Mtx(b'\x01\x00\x00\x00', txin1, txout1, b'\x00\x00\x00\x00')
        tx2 = mtx.Mtx(b'\x01\x00\x00\x00', txin1, txout1, b'\x00\x00\x00\x00')
        tx3 = mtx.Mtx(b'\x01\x00\x00\x00', txin1, txout2, b'\x00\x00\x00\x00')
        tx4 = mtx.Mtx(b'\x01\x00\x00\x00', txin2, txout1, b'\x00\x00\x00\x00')
        tx5 = mtx.Mtx(b'\x02\x00\x00\x00', txin1, txout1, b'\x00\x00\x00\x00')
        tx6 = mtx.Mtx(b'\x01\x00\x00\x00', txin1, txout1, b'\x01\x00\x00\x00')
        self.assertEqual(tx1, tx2)
        self.assertNotEqual(tx1, tx3)
        self.assertNotEqual(tx1, tx4)
        self.assertNotEqual(tx1, tx5)
        self.assertNotEqual(tx1, tx6)

    def test_bytes(self):
        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            sequence=b'\xff\xff\xff\xff')]
        txout = [
            mtx.TxOutput(b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        tx = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')

        self.assertEqual(bytes(tx), b''.join([b'\x01\x00\x00\x00',
                                              b'\x01txid\x04\x06script\xff\xff\xff\xff',
                                              b'\x01\x88\x13\x00\x00\x00\x00\x00\x00\rscript_pubkey',
                                              b'\x00\x00\x00\x00']))

    def test_bytes_segwit(self):
        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            b'witness', sequence=b'\xff\xff\xff\xff')]
        txout = [
            mtx.TxOutput(b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        tx = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')

        self.assertEqual(bytes(tx), b''.join([b'\x01\x00\x00\x00', b'\x00\x01',
                                              b'\x01txid\x04\x06script\xff\xff\xff\xff',
                                              b'\x01\x88\x13\x00\x00\x00\x00\x00\x00\rscript_pubkey',
                                              b'witness',
                                              b'\x00\x00\x00\x00']))

    def test_is_segwit(self):
        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            sequence=b'\xff\xff\xff\xff')]
        txout = [
            mtx.TxOutput(b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        tx = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')
        self.assertFalse(mtx.Mtx.is_segwit(tx))
        self.assertFalse(mtx.Mtx.is_segwit(bytes(tx)))
        self.assertFalse(mtx.Mtx.is_segwit(bytes(tx).hex()))

        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            b'witness', sequence=b'\xff\xff\xff\xff')]
        txout = [
            mtx.TxOutput(b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        tx = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')
        self.assertTrue(mtx.Mtx.is_segwit(tx))
        self.assertTrue(mtx.Mtx.is_segwit(bytes(tx)))
        self.assertTrue(mtx.Mtx.is_segwit(bytes(tx).hex()))


@unittest.skip
class TestTxId(unittest.TestCase):

    def test_calc_txid_legacy(self):
        self.assertEqual(mtx.calc_txid(
            FINAL_TX_1), 'e6922a6e3f1ff422113f15543fbe1340a727441202f55519640a70ac4636c16f')

    def test_calc_txid_segwit(self):
        self.assertEqual(mtx.calc_txid(
            SEGWIT_TX_1), 'a103ed36e9afee8b4001b1c3970ba8cd9839ff95e8b8af3fbe6016f6287bf9c6')


@unittest.skip
class TestEstimateTxFee(unittest.TestCase):

    def test_accurate_compressed(self):
        self.assertEqual(mtx.estimate_tx_fee(148, 1, 68, 2, 70), 15820)

    def test_accurate_uncompressed(self):
        self.assertEqual(mtx.estimate_tx_fee(180, 1, 68, 2, 70), 18060)

    def test_none(self):
        self.assertEqual(mtx.estimate_tx_fee(740, 5, 170, 5, 0), 0)


@unittest.skip
class TestSanitizeTxData(unittest.TestCase):

    def test_no_input(self):
        with self.assertRaises(ValueError):
            mtx.sanitize_tx_data([], [], 70, '')

    def test_message(self):
        unspents_original = [mtx.UTXO(10000, 0, '', '', 0),
                             mtx.UTXO(10000, 0, '', '', 0)]
        outputs_original = [(BITCOIN_ADDRESS_TEST, 1000, 'satoshi')]

        unspents, outputs = mtx.sanitize_tx_data(
            unspents_original, outputs_original, fee_amount=5, leftover=RETURN_ADDRESS,
            combine=True, message='hello', version='test'
        )

        self.assertEqual(len(outputs), 3)
        self.assertEqual(outputs[2][0], b'hello')
        self.assertEqual(outputs[2][1], 0)

    def test_fee_applied(self):
        unspents_original = [mtx.UTXO(1000, 0, '', '', 0),
                             mtx.UTXO(1000, 0, '', '', 0)]
        outputs_original = [(BITCOIN_ADDRESS, 2000, 'satoshi')]

        with self.assertRaises(mtx.InsufficientFunds):
            mtx.sanitize_tx_data(
                unspents_original, outputs_original, fee_amount=1, leftover=RETURN_ADDRESS,
                combine=True, message=None
            )

    def test_zero_remaining(self):
        unspents_original = [mtx.UTXO(1000, 0, '', '', 0),
                             mtx.UTXO(1000, 0, '', '', 0)]
        outputs_original = [(BITCOIN_ADDRESS_TEST, 2000, 'satoshi')]

        unspents, outputs = mtx.sanitize_tx_data(
            unspents_original, outputs_original, fee_amount=0, leftover=RETURN_ADDRESS,
            combine=True, message=None, version='test'
        )

        self.assertEqual(unspents, unspents_original)
        self.assertEqual(outputs, [(BITCOIN_ADDRESS_TEST, 2000)])

    def test_combine_remaining(self):
        unspents_original = [mtx.UTXO(1000, 0, '', '', 0),
                             mtx.UTXO(1000, 0, '', '', 0)]
        outputs_original = [(BITCOIN_ADDRESS_TEST, 500, 'satoshi')]

        unspents, outputs = mtx.sanitize_tx_data(
            unspents_original, outputs_original, fee_amount=0, leftover=RETURN_ADDRESS,
            combine=True, message=None, version='test'
        )

        self.assertEqual(unspents, unspents_original)
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[1][0], RETURN_ADDRESS)
        self.assertEqual(outputs[1][1], 1500)

    def test_combine_insufficient_funds(self):
        unspents_original = [mtx.UTXO(1000, 0, '', '', 0),
                             mtx.UTXO(1000, 0, '', '', 0)]
        outputs_original = [(BITCOIN_ADDRESS_TEST, 2500, 'satoshi')]

        with self.assertRaises(mtx.InsufficientFunds):
            mtx.sanitize_tx_data(
                unspents_original, outputs_original, fee_amount=50, leftover=RETURN_ADDRESS,
                combine=True, message=None, version='test'
            )

    def test_no_combine_remaining(self):
        unspents_original = [mtx.UTXO(7000, 0, '', '', 0),
                             mtx.UTXO(3000, 0, '', '', 0)]
        outputs_original = [(BITCOIN_ADDRESS_TEST, 2000, 'satoshi')]

        unspents, outputs = mtx.sanitize_tx_data(
            unspents_original, outputs_original, fee_amount=0, leftover=RETURN_ADDRESS,
            combine=False, message=None, version='test'
        )

        self.assertEqual(len(unspents), 1)
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[1][0], RETURN_ADDRESS)
        self.assertEqual(outputs[1][1], unspents[0].amount - 2000)

    def test_no_combine_with_fee(self):
        """
        Verify that unused unspents do not increase fee.
        """
        unspents_single = [mtx.UTXO(5000, 0, '', '', 0)]
        unspents_original = [mtx.UTXO(5000, 0, '', '', 0),
                             mtx.UTXO(5000, 0, '', '', 0)]
        outputs_original = [(RETURN_ADDRESS, 1000, 'satoshi')]

        unspents, outputs = mtx.sanitize_tx_data(
            unspents_original, outputs_original, fee_amount=1, leftover=RETURN_ADDRESS,
            combine=False, message=None, version='test'
        )

        unspents_single, outputs_single = mtx.sanitize_tx_data(
            unspents_single, outputs_original, fee_amount=1, leftover=RETURN_ADDRESS,
            combine=False, message=None, version='test'
        )

        self.assertEqual(unspents, [mtx.UTXO(5000, 0, '', '', 0)])
        self.assertEqual(unspents_single, [mtx.UTXO(5000, 0, '', '', 0)])
        self.assertEqual(len(outputs), 2)
        self.assertEqual(len(outputs_single), 2)
        self.assertEqual(outputs[1][0], RETURN_ADDRESS)
        self.assertEqual(outputs_single[1][0], RETURN_ADDRESS)
        self.assertEqual(outputs[1][1], outputs_single[1][1])

    def test_no_combine_insufficient_funds(self):
        unspents_original = [mtx.UTXO(1000, 0, '', '', 0),
                             mtx.UTXO(1000, 0, '', '', 0)]
        outputs_original = [(BITCOIN_ADDRESS_TEST, 2500, 'satoshi')]

        with self.assertRaises(mtx.InsufficientFunds):
            mtx.sanitize_tx_data(
                unspents_original, outputs_original, fee_amount=50, leftover=RETURN_ADDRESS,
                combine=False, message=None
            )

    def test_no_combine_mainnet_with_testnet(self):
        unspents = [mtx.UTXO(20000, 0, '', '', 0)]
        outputs = [(BITCOIN_ADDRESS, 500, 'satoshi'),
                   (BITCOIN_ADDRESS_TEST, 500, 'satoshi')]

        with self.assertRaises(ValueError):
            mtx.sanitize_tx_data(
                unspents, outputs, fee_amount=50, leftover=RETURN_ADDRESS,  # leftover is a testnet-address
                combine=False, message=None, version='main'
            )

        with self.assertRaises(ValueError):
            mtx.sanitize_tx_data(
                # leftover is a mainnet-address
                unspents, outputs, fee_amount=50, leftover=BITCOIN_ADDRESS,
                combine=False, message=None, version='main'
            )


@unittest.skip
class TestAddressToScriptPubKeyReal(unittest.TestCase):

    def test_address_to_scriptpubkey_legacy(self):
        want = b'v\xa9\x14\x92F\x1b\xdeb\x83\xb4a\xec\xe7\xdd\xf4\xdb\xf1\xe0\xa4\x8b\xd1\x13\xd8\x88\xac'
        self.assertEqual(util.address_to_scriptpubkey(BITCOIN_ADDRESS), want)

        want = b'v\xa9\x14\x99\x0e\xf6\rc\xb5\xb5\x96J\x1c"\x82\x06\x1a\xf4Q#\xe9?\xcb\x88\xac'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_ADDRESS_COMPRESSED), want)

    def test_address_to_scriptpubkey_legacy_ltc(self):
        want = 'a914271c1bad2ebfec5ed79e999b99b092881284d79587'
        self.assertEqual(util.address_to_scriptpubkey(
            LITECOIN_ADDRESS).hex(), want)

    def test_address_to_scriptpubkey_legacy_p2sh(self):
        want = b'\xa9\x14U\x13\x1e\xfbz\x0e\xddLv\xcc;\xbe\x83;\xfcY\xa6\xf7<k\x87'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_ADDRESS_PAY2SH), want)

    def test_address_to_scriptpubkey_bech32(self):
        want = b'\x00\x14\xe8\xdf\x01\x8c~2l\xc2S\xfa\xac~F\xcd\xc5\x1ehT,B'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_SEGWIT_ADDRESS), want)

    def test_address_to_scriptpubkey_bech32_p2sh(self):
        want = b'\x00 \xc7\xa1\xf1\xa4\xd6\xb4\xc1\x80*Yc\x19f\xa1\x83Y\xdew\x9e\x8aje\x9775\xa3\xcc\xdf\xda\xbc@}'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_SEGWIT_ADDRESS_PAY2SH), want)

    def test_address_to_scriptpubkey_legacy_test(self):
        want = b'v\xa9\x14\x92F\x1b\xdeb\x83\xb4a\xec\xe7\xdd\xf4\xdb\xf1\xe0\xa4\x8b\xd1\x13\xd8\x88\xac'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_ADDRESS_TEST), want)

        want = b'v\xa9\x14\x99\x0e\xf6\rc\xb5\xb5\x96J\x1c"\x82\x06\x1a\xf4Q#\xe9?\xcb\x88\xac'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_ADDRESS_TEST_COMPRESSED), want)

    def test_address_to_scriptpubkey_legacy_p2sh_test(self):
        want = b'\xa9\x14\xf2&\x1e\x95d\xc9\xdf\xff\xa8\x15\x05\xc1S\xfb\x95\xbf\x93\x99C\x08\x87'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_ADDRESS_TEST_PAY2SH), want)

    def test_address_to_scriptpubkey_bech32_test(self):
        want = b'\x00\x14u\x1ev\xe8\x19\x91\x96\xd4T\x94\x1cE\xd1\xb3\xa3#\xf1C;\xd6'
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_SEGWIT_ADDRESS_TEST.lower()), want)
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_SEGWIT_ADDRESS_TEST.upper()), want)

    def test_address_to_scriptpubkey_bech32_p2sh_test(self):
        want = b"\x00 \x18c\x14<\x14\xc5\x16h\x04\xbd\x19 3V\xda\x13l\x98Vx\xcdM'\xa1\xb8\xc62\x96\x04\x902b"
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_SEGWIT_ADDRESS_TEST_PAY2SH.lower()), want)
        self.assertEqual(util.address_to_scriptpubkey(
            BITCOIN_SEGWIT_ADDRESS_TEST_PAY2SH.upper()), want)

    def test_address_to_scriptpubkey_invalid_checksum(self):
        address_invalid = BITCOIN_ADDRESS[:6] + "error" + BITCOIN_ADDRESS[11:]
        with self.assertRaises(util.ConvertionError):
            util.address_to_scriptpubkey(address_invalid)

        address_invalid = BITCOIN_ADDRESS_PAY2SH[:6] + \
            "error" + BITCOIN_ADDRESS_PAY2SH[11:]
        with self.assertRaises(util.ConvertionError):
            util.address_to_scriptpubkey(address_invalid)

        address_invalid = BITCOIN_SEGWIT_ADDRESS[:6] + \
            "error" + BITCOIN_SEGWIT_ADDRESS[11:]
        with self.assertRaises(util.ConvertionError):
            util.address_to_scriptpubkey(address_invalid)

    def test_address_to_scriptpubkey_invalid_address(self):
        address_invalid = "X" + BITCOIN_ADDRESS[1:]
        with self.assertRaises(util.ConvertionError):
            util.address_to_scriptpubkey(address_invalid)

        address_invalid = "X" + BITCOIN_ADDRESS_PAY2SH[1:]
        with self.assertRaises(util.ConvertionError):
            util.address_to_scriptpubkey(address_invalid)

        address_invalid = "X" + BITCOIN_SEGWIT_ADDRESS[1:]
        with self.assertRaises(util.ConvertionError):
            util.address_to_scriptpubkey(address_invalid)


@unittest.skip
class TestDeserializeTransaction(unittest.TestCase):

    def test_legacy_deserialize(self):
        txobj = mtx.deserialize(FINAL_TX_1)
        self.assertEqual(txobj.version, util.hex_to_bytes(FINAL_TX_1[:8]))
        self.assertEqual(len(txobj.TxIn), 1)
        self.assertEqual(txobj.TxIn[0].txid,
                         util.hex_to_bytes(FINAL_TX_1[10:74]))
        self.assertEqual(txobj.TxIn[0].txindex,
                         util.hex_to_bytes(FINAL_TX_1[74:82]))
        self.assertEqual(txobj.TxIn[0].script_sig_len,
                         util.hex_to_bytes(FINAL_TX_1[82:84]))
        self.assertEqual(txobj.TxIn[0].script_sig,
                         util.hex_to_bytes(FINAL_TX_1[84:360]))
        self.assertEqual(txobj.TxIn[0].witness, b'')
        self.assertEqual(txobj.TxIn[0].sequence,
                         util.hex_to_bytes(FINAL_TX_1[360:368]))
        self.assertEqual(len(txobj.TxOut), 2)
        self.assertEqual(txobj.TxOut[0].amount,
                         util.hex_to_bytes(FINAL_TX_1[370:386]))
        self.assertEqual(txobj.TxOut[0].script_pubkey_len,
                         util.hex_to_bytes(FINAL_TX_1[386:388]))
        self.assertEqual(txobj.TxOut[0].script_pubkey,
                         util.hex_to_bytes(FINAL_TX_1[388:438]))
        self.assertEqual(txobj.TxOut[1].amount,
                         util.hex_to_bytes(FINAL_TX_1[438:454]))
        self.assertEqual(txobj.TxOut[1].script_pubkey_len,
                         util.hex_to_bytes(FINAL_TX_1[454:456]))
        self.assertEqual(txobj.TxOut[1].script_pubkey,
                         util.hex_to_bytes(FINAL_TX_1[456:506]))
        self.assertEqual(txobj.locktime, util.hex_to_bytes(FINAL_TX_1[506:]))

    def test_segwit_deserialize(self):
        txobj = mtx.deserialize(SEGWIT_TX_1)
        self.assertEqual(txobj.version, util.hex_to_bytes(SEGWIT_TX_1[:8]))
        self.assertEqual(len(txobj.TxIn), 2)
        self.assertEqual(txobj.TxIn[0].txid,
                         util.hex_to_bytes(SEGWIT_TX_1[14:78]))
        self.assertEqual(txobj.TxIn[0].txindex,
                         util.hex_to_bytes(SEGWIT_TX_1[78:86]))
        self.assertEqual(txobj.TxIn[0].script_sig_len,
                         util.hex_to_bytes(SEGWIT_TX_1[86:88]))
        self.assertEqual(txobj.TxIn[0].script_sig,
                         util.hex_to_bytes(SEGWIT_TX_1[88:300]))
        self.assertEqual(txobj.TxIn[0].sequence,
                         util.hex_to_bytes(SEGWIT_TX_1[300:308]))
        self.assertEqual(txobj.TxIn[0].witness,
                         util.hex_to_bytes(SEGWIT_TX_1[564:566]))
        self.assertEqual(txobj.TxIn[1].txid,
                         util.hex_to_bytes(SEGWIT_TX_1[308:372]))
        self.assertEqual(txobj.TxIn[1].txindex,
                         util.hex_to_bytes(SEGWIT_TX_1[372:380]))
        self.assertEqual(txobj.TxIn[1].script_sig_len,
                         util.hex_to_bytes(SEGWIT_TX_1[380:382]))
        self.assertEqual(txobj.TxIn[1].script_sig,
                         util.hex_to_bytes(SEGWIT_TX_1[382:428]))
        self.assertEqual(txobj.TxIn[1].sequence,
                         util.hex_to_bytes(SEGWIT_TX_1[428:436]))
        self.assertEqual(txobj.TxIn[1].witness,
                         util.hex_to_bytes(SEGWIT_TX_1[566:780]))
        self.assertEqual(len(txobj.TxOut), 2)
        self.assertEqual(txobj.TxOut[0].amount,
                         util.hex_to_bytes(SEGWIT_TX_1[438:454]))
        self.assertEqual(txobj.TxOut[0].script_pubkey_len,
                         util.hex_to_bytes(SEGWIT_TX_1[454:456]))
        self.assertEqual(txobj.TxOut[0].script_pubkey,
                         util.hex_to_bytes(SEGWIT_TX_1[456:500]))
        self.assertEqual(txobj.TxOut[1].amount,
                         util.hex_to_bytes(SEGWIT_TX_1[500:516]))
        self.assertEqual(txobj.TxOut[1].script_pubkey_len,
                         util.hex_to_bytes(SEGWIT_TX_1[516:518]))
        self.assertEqual(txobj.TxOut[1].script_pubkey,
                         util.hex_to_bytes(SEGWIT_TX_1[518:564]))
        self.assertEqual(txobj.locktime, util.hex_to_bytes(SEGWIT_TX_1[780:]))


@unittest.skip
class TestSignTx(unittest.TestCase):

    def test_sign_tx_legacy_input(self):
        key_ = key.PrivateKey.from_wif(WALLET_FORMAT_COMPRESSED_MAIN)
        txobj = mtx.deserialize(UNSIGNED_TX_SEGWIT)
        tx = mtx.sign_tx(key_, txobj, unspents=[UNSPENTS_SEGWIT[0]])
        # TODO:
        # self.assertEqual(tx[:380], FINAL_TX_SEGWIT[:380])
        # to test it online
        # log.info(f"PUBKEY: {key_.P2PKH} \n SW:{key_.P2WPKH} \n TX:{tx}")

    def test_sign_tx_invalid_unspents(self):
        key_ = key.PrivateKey.from_wif(WALLET_FORMAT_TEST_1)
        txobj = mtx.deserialize(UNSIGNED_TX_SEGWIT)
        with self.assertRaises(TypeError):
            # Unspents must be presented as list:
            mtx.sign_tx(key_, txobj, unspents=UNSPENTS_SEGWIT[0])

    def test_sign_tx_invalid_segwit_no_amount(self):
        key_ = key.PrivateKey.from_wif(WALLET_FORMAT_TEST_1)
        txobj = mtx.deserialize(UNSIGNED_TX_SEGWIT)
        unspents = copy.deepcopy(UNSPENTS_SEGWIT)
        unspents[1].amount = None
        self.assertTrue(mtx.Mtx.is_segwit(txobj))
        with self.assertRaises(ValueError):
            mtx.sign_tx(key_, txobj, unspents=unspents)


@unittest.skip
class TestCreateSignedTransaction(unittest.TestCase):

    def test_matching(self):
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_MAIN)
        tx = mtx.create_new_transaction(private_key, UNSPENTS, OUTPUTS)
        self.assertEqual(tx[-288:], FINAL_TX_1[-288:])

    def test_segwit_transaction(self):
        outputs = [("2NEcbT1xeB7488HqpmXeC2u5zqYFQ5n4x5Q", 50000000),
                   ("2N21Gzex7WJCzzsA5D33nofcnm1dYSKuJzT", 149990000)]
        private_key = key.PrivateKey.from_wif(WALLET_FORMAT_TEST_1)
        tx = mtx.create_new_transaction(private_key, UNSPENTS_SEGWIT, outputs)
        # TODO:
        #log.info(f"PUBKEY: {private_key.P2PKH} \n SW:{private_key.P2WPKH} \n TX:{tx}")
        # self.assertEqual(tx , FINAL_TX_SEGWIT)

@unittest.skip
class TestSelectCoins(unittest.TestCase):
    def test_perfect_match(self):
        unspents, remaining = mtx.select_coins(100000000, 0, [34, 34], 0, absolute_fee=True,
                                               consolidate=False, unspents=UNSPENTS_SEGWIT)
        self.assertEqual(len(unspents), 1)
        self.assertEqual(remaining, 0)

    def test_perfect_match_with_range(self):
        unspents, remaining = mtx.select_coins(99960000, 200, [34, 34], 0, absolute_fee=True,
                                               consolidate=False, unspents=UNSPENTS_SEGWIT)
        self.assertEqual(len(unspents), 1)
        self.assertEqual(remaining, 0)

    def test_random_draw(self):
        unspents, remaining = mtx.select_coins(150000000, 0, [34, 34], 0, absolute_fee=True,
                                               consolidate=False, unspents=UNSPENTS_SEGWIT)
        self.assertTrue(all([u in UNSPENTS_SEGWIT for u in unspents]))
        self.assertEqual(remaining, 50000000)


@unittest.skip
class TestBtcTx(unittest.TestCase):

    @skip
    def test_sighash(self):
        body = json.loads(TEST_DATA_PATH.joinpath("sighash.json").read_text())
        for idx, group in enumerate(body):
            # description
            if idx == 0:
                continue
                # raw_transaction, script, input_index, hashType, signature_hash (result)
            # self.assertEqual( mtx.calc_txid(group[0]) , group[-1] , idx )
            # TODO:

            tx = mtx.deserialize(group[0])
            tx_id = mtx.calc_txid(group[0])
            #log.info(f"\n{idx} IDX:{group[2]} SCR:{group[1]}")
            #log.info(f"sighash: {group[-1]} ")
            #log.info(f"txid: {tx_id}")

            #inps = tx.TxIn
            # for inp in inps:
           #     log.warning(f"INP {inp.txindex} SIG:{inp.script_sig}")

    def test_valid(self):
        """
        It is important test but it doesn't check what expected !!!
        it validate current deserealization api only for a while
        TODO:
        """
        body = json.loads(TEST_DATA_PATH.joinpath("tx_valid.json").read_text())
        for idx, group in enumerate(body):
            # if len(group) == 1:
            #   log.info("\n" +group[0])
            #    continue
            if not isinstance(group[0], list) \
                    or 3 != len(group) \
                or not isinstance(group[1], str) \
                    or not isinstance(group[2], str):
                continue
            # inputs
            txins = []
            for inp in group[0]:
                if not isinstance(inp, list) or len(inp) not in [3, 4]:
                    continue
                outpoint = (inp[0], inp[1])
                script = inp[2]
                amount = inp[3] if len(inp) > 3 else None
                # TODO:
                txin = mtx.TxInput(
                    script, outpoint[0], outpoint[1], amount=amount)
                if txin.txindex >= 0:
                    txins.append(txin)
            # tx
            tx = mtx.deserialize(group[1])
            inps = tx.TxIn
            for has, must in zip(inps, txins):
                self.assertEqual(must.txindex, int.from_bytes(
                    has.txindex, byteorder='little'))
                self.assertEqual(has.script_sig, has.script_sig)
                self.assertEqual(has.amount, has.amount)
                #log.warning(f"+++ {has.script_sig} == {has.script_sig}")

    def test_invalid(self):
        """
        TODO:
        """
        body = json.loads(TEST_DATA_PATH.joinpath(
            "tx_invalid.json").read_text())
        for idx, group in enumerate(body):
            if not isinstance(group[0], list) \
                    or 3 != len(group) \
                or not isinstance(group[1], str) \
                    or not isinstance(group[2], str):
                continue
            # inputs
            txins = []
            for inp in group[0]:
                if not isinstance(inp, list) or len(inp) not in [3, 4]:
                    continue
                outpoint = (inp[0], inp[1])
                script = inp[2]
                amount = inp[3] if len(inp) > 3 else None
                # TODO:
                txin = mtx.TxInput(
                    script, outpoint[0], outpoint[1], amount=amount)
                if txin.txindex >= 0:
                    txins.append(txin)
            # tx
            tx = mtx.deserialize(group[1])
            inps = tx.TxIn
            for has, must in zip(inps, txins):
                #self.assertEqual( must.txindex, int.from_bytes(has.txindex, byteorder='little'), group[0])
                self.assertEqual(has.script_sig, has.script_sig)
                self.assertEqual(has.amount, has.amount, group[0])


@skip("ENABLE IT ASAP")
class TestMakeMtxReal(unittest.TestCase):

    def test_legacy(self):
        UTXOS = [
            # {"tx":"0a8e8b9a3a009627309a3e547d7463c6d3414189c0f6d91c998fb7035a2544e0","script":None,"index":1,"height": 	1747044,
            # "amount":385684,},
            {"tx": "589652f6985da46526cb7d7173b1f53a7ab6b80492615b5089e37e74606e9579",
                "script": None, "index": 1, "height": 1747241, "amount": 10000, }
        ]
        # n3g1NYG9Nh82u9tFKaueMg3XGzqWPzihbh
        self._make_tx(
            UTXOS,
            'cV9Wn1AbuhhotvfYouaJnQNaLa1x9H5h11mhZnV8tJwyLQjUW1Ap',
            'mmdzo9UNYq6mkcoA2FcDdZSMVJnD91HRW9',
            'n4JftWMw4GVcQSe91PpDRc4ysbpA95Ds9e',
            False,
        )

    def test_segwit(self):
        UTXOS = [
            # {"tx":"0a8e8b9a3a009627309a3e547d7463c6d3414189c0f6d91c998fb7035a2544e0","script":"0014af2f09f62030b08a247e470283ff63a48b247b4a","index":1,"height": 1747044,
            #     "amount":100000 ,}
            {"tx": "c0fe4998cd4608a1732d061fd36a1dc282ce8b2f7dc7dd7d7ab9aa3eb256427a", "script": None, "index": 0, "height": 1747044,
                "amount": 100000, }
        ]
        ###
        # tb1qdqfrpchephv29plzxym9wlek5zgyearwqgr878
        self._make_tx(
            UTXOS,
            'cVumXVPVCN4DGZGJFDCLV9r8tpYmv4QE4LAMePHUid1dCHMtggZF',
            'tb1q4uhsna3qxzcg5fr7gupg8lmr5j9jg762a3e79s',
            'tb1qppkvrl7wmacp4nmr8kyvk5ngj84nw7588ch95y',
            True,
        )
        # https://live.blockcypher.com/btc-testnet/tx/f88fe4673ed5e304fbf4ff70bb994c356245cbb5bfb2f5da2c41c7dd50438d91/

    def test_no_script(self):
        UTXOS = [
            {"tx": "f88fe4673ed5e304fbf4ff70bb994c356245cbb5bfb2f5da2c41c7dd50438d91", "script": None, "index": 0, "height": 1665002,
             "amount": 950000, },
        ]
        # n3g1NYG9Nh82u9tFKaueMg3XGzqWPzihbh
        self._make_tx(
            UTXOS,
            'cVYLX3jcXGfLHEbcyDBqR7pTWpnWAFBk5YGbVpHTWsdFJrgGRwXQ',
            'tb1qhl5pmpxrrcdq76tq3rcd2tgdvn9ltd497w80zk',
            'tb1qdqfrpchephv29plzxym9wlek5zgyearwqgr878',
            True,
        )

    def test_ltc(self):
        UTXOS = [
            {"tx": "d61014fc6ac5884400c57de8d4dae035a6b657f60691d1e9d58ba75cac0a5e40", "script": None, "index": 1, "height": 1787808,
             "amount": 1000000, },
        ]
        self._make_tx(
            UTXOS,
            'T9A6nmE9d7JXX6zx67HPMpuZyiKWKAd9Mas5ZPDCYD5fhvNpxL3d',
            'LQLno78Wtcme98eJ8YVii9u8eVvFbKeKUi',
            'MBTxFu14TeomwAMvzL8CBXGj5mH6zcKuHZ',
            False,
        )

    def _make_tx(self, utxos, wif, source, target, segwit: bool, *, broadcast: bool = True, network=None):
        from bmnclient.wallet import script
        import requests
        ###
        type_ = 'p2wpkh' if segwit else "p2pkh"
        # prv key
        # TODO: export real key !!!
        prv = key.PrivateKey.from_wif(wif, network)
        pub = prv.public_key
        self.assertEqual(pub.P2WPKH if segwit else pub.P2PKH, source)
        for ut in utxos:
            if ut['script'] is not None:
                res = script.parse_script(ut['script'], segwit)
                log.warning(f"res: {res}")
                self.assertEqual(util.hash160(pub.data), res['addressHash'])
                self.assertEqual(type_.upper(), res['type'])

        full_amount = sum(u['amount'] for u in utxos)
        # outs
        outputs = [
            (target,   int(full_amount * 0.9)),
        ]
        # unspents

        def make_unspent(table):
            return mtx.UTXO(
                amount=table['amount'],
                txid=table['tx'],
                txindex=table['index'],
                script=table['script'],
                type=type_
            )
        unspents = list(map(make_unspent, utxos))
        log.info(f"\ntargets: {outputs} ")
        log.info(f"\nUNSPENTS: {unspents}")
        # tx
        # tx = mtx.create_new_transaction(prv, unspents, outputs)
        mtx_ = mtx.Mtx.make(unspents, outputs)
        tx_ = mtx_.to_tx(None)
        log.warning("TX: %r" % tx_)
        self.assertEqual(tx_.balance + tx_.feeAmount, full_amount)
        tx = mtx_.sign(prv, unspents=unspents)

        log.warning(f"RAW: {tx}")

        if broadcast:
            headers = {"Content-type": "application/vnd.api+json"}
            coin_tag = coins.network_tag(prv.network)
            res = requests.post(f"https://d1.bitmarket.network:30110/v1/coins/{coin_tag}/tx/broadcast", json={
                "data": {
                    "type": "tx_broadcast",
                    "attributes": {
                        "data": tx,
                    }
                }
            },
                headers=headers,
            )
            if 200 != res.status_code:
                log.error(f"resp code: {res.status_code} errors:{res.text}")
            else:
                log.info(f"result: {res.text}")
        # https://live.blockcypher.com/btc-testnet/tx/e80dcb5ee9b1705f7929d5c5e123667ada98cbcd26d645081fe17827a4f90415/


@unittest.skip
class TestCalculatePreimages(unittest.TestCase):

    def test_calculate_preimages(self):
        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            b'witness', sequence=b'\xff\xff\xff\xff')]
        txout = [mtx.TxOutput(
            b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        txobj = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')

        want = b'yI\x8d\x99H\xcb\xe3\x88\xce\x83}\xc1\xfc\xaf\xf7\xd5\\\xf67\x93\x86\xb5\xc7M\xd1\xdb\xd2LyJ`<'
        self.assertEqual(txobj.calc_preimages(
            [(0, constants.HASH_TYPE, False)])[0], want)

        want = b'\xed\x85\xc1\x0f\xc2\xb1\xc9\x05\xbf\xa6S\x15\xba$\x84\xad\x14\x8dni\x17\x1eD\xd6\xf7e\xd8\x0e\xfb\x05\x93\x1a'
        self.assertEqual(txobj.calc_preimages(
            [(0, constants.HASH_TYPE, True)])[0], want)

    def test_calculate_preimages_unsupported_hashtypes(self):
        txin = [mtx.TxInput(b'script', b'txid', b'\x04',
                            b'witness', sequence=b'\xff\xff\xff\xff')]
        txout = [mtx.TxOutput(
            b'\x88\x13\x00\x00\x00\x00\x00\x00', b'script_pubkey')]
        txobj = mtx.Mtx(b'\x01\x00\x00\x00', txin, txout, b'\x00\x00\x00\x00')

        with self.assertRaises(ValueError):
            txobj.calc_preimages([(0, b'\x02\x00\x00\x00', False)])

        with self.assertRaises(ValueError):
            txobj.calc_preimages([(0, b'\x03\x00\x00\x00', False)])

        with self.assertRaises(ValueError):
            txobj.calc_preimages([(0, b'\x81\x00\x00\x00', False)])

        with self.assertRaises(ValueError):
            txobj.calc_preimages([(0, b'\x04\x00\x00\x00', False)])


@unittest.skip
class TestMultiSourceReal(unittest.TestCase):

    def test_segwit(self):
        SOURCES = [
            # {"tx":"0a8e8b9a3a009627309a3e547d7463c6d3414189c0f6d91c998fb7035a2544e0","script":"0014af2f09f62030b08a247e470283ff63a48b247b4a","index":1,"height": 1747044,
            #     "amount":100000 ,}
            ([{"tx": "8f6f5310f170dac0460ea9b32ab9e8945ce7c6ab2e91253aaf6e89ac7b5ec619", "script": None, "index": 0, "height": 1767768,
                "amount": 1000, }], "cNpqT8qf6JWMWzEhzfrWzDdN9SM4rCkQsV63Z71gM3HwBU2LMQzt", "tb1qyeekvm79yusgc05l58aw0gzvk7wddkkzxhvule"),
            ([{"tx": "45241c3dd41a33b74e7cb5af8fdd1cc9e69d96c9e8cd33ffa12a7d786c8bf8c9", "script": None, "index": 1, "height": 1767728,
                "amount": 696, }], "cVumXVPVCN4DGZGJFDCLV9r8tpYmv4QE4LAMePHUid1dCHMtggZF", "tb1q4uhsna3qxzcg5fr7gupg8lmr5j9jg762a3e79s"),
        ]
        ###
        # tb1qdqfrpchephv29plzxym9wlek5zgyearwqgr878
        self._make_tx(
            SOURCES,
            'tb1qppkvrl7wmacp4nmr8kyvk5ngj84nw7588ch95y',
            True,
        )

    def _make_tx(self, sources: List[Tuple[dict, str, str]], target, segwit: bool, *, broadcast: bool = True, network=None):
        """[summary]

        Args:
            sources (List[Tuple[ dict,str,str ]]): ( UTXO, WIF , ADDRESS )
            target ([type]): [description]
            segwit (bool): [description]
            broadcast (bool, optional): [description]. Defaults to True.
            network ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """

        from bmnclient.wallet import script
        import requests
        ###
        type_ = 'p2wpkh' if segwit else "p2pkh"
        full_amount = 0

        def make_unspent(table):
            return mtx.UTXO(
                amount=table['amount'],
                txid=table['tx'],
                txindex=table['index'],
                script=table['script'],
                type=type_
            )

        def do_source(utxo, wif, addr) -> List[Tuple[mtx.UTXO, key.PrivateKey]]:
            log.debug(f" == {utxo}")
            prv = key.PrivateKey.from_wif(wif, network)
            pub = prv.public_key
            nonlocal full_amount
            full_amount += sum(u["amount"] for u in utxo)
            self.assertEqual(pub.P2WPKH if segwit else pub.P2PKH, addr)
            for ut in utxo:
                if ut['script'] is not None:
                    res = script.parse_script(ut['script'], segwit)
                    log.warning(f"res: {res}")
                    self.assertEqual(util.hash160(
                        pub.data), res['addressHash'])
                    self.assertEqual(type_.upper(), res['type'])
            return prv, [make_unspent(ut) for ut in utxo]

        # unspents
        unspents_to_sign = [do_source(*s) for s in sources]
        unspents_shared = sum((u for _, u in unspents_to_sign) , [])
        # outs
        outputs = [
            (target,   int(full_amount * 0.5)),
        ]

        log.info(f"\ntargets: {outputs} ")
        log.info(f"\nUNSPENTS: {unspents_shared}")
        # tx
        # tx = mtx.create_new_transaction(prv, unspents, outputs)
        mtx_ = mtx.Mtx.make(unspents_shared, outputs)
        tx_ = mtx_.to_tx()
        log.warning("TX: %r" % tx_)
        self.assertEqual(tx_.balance + tx_.feeAmount, full_amount)
        coin_tag = coins.network_tag(unspents_to_sign[0][0].network)
        for p, u in unspents_to_sign:
            mtx_.sign(p, unspents=u)
        tx = mtx_.to_hex()

        log.warning(f"RAW: {tx}")

        if broadcast:
            headers = {"Content-type": "application/vnd.api+json"}
            res = requests.post(f"https://d1.bitmarket.network:30110/v1/coins/{coin_tag}/tx/broadcast", json={
                "data": {
                    "type": "tx_broadcast",
                    "attributes": {
                        "data": tx,
                    }
                }
            },
                headers=headers,
            )
            if 200 != res.status_code:
                log.error(f"resp code: {res.status_code} errors:{res.text}")
            else:
                log.info(f"result: {res.text}")
