
import logging
import os
import unittest

from client import gcd
from client.ui.gui import coin_manager, tx_controller
from client.wallet import coin_network, coins, fee_manager, hd, key, mutable_tx
from client.wallet import mtx_impl as mtx
# from . import test_mtx


log = logging.getLogger(__name__)

UNSPENTS_SEGWIT = [
    mtx.UTXO(1000000,
             1,
             '76a914905aa72f3d1747094a24d3adbc38905bb451ffc888ac',
             'f09c22717770fcd7e477953c3ca7ecb9bd44ec4d5392f24fdd247dbb8db2d388',
             0,
             'p2wpkh'),
    mtx.UTXO(1000000,
             1,
             # 'a9146015d175e191e6e5b99211e3ffc6ea7658cb051a87', !!!
             '0014905aa72f3d1747094a24d3adbc38905bb451ffc8',
             'f42c4ee1f95a3c9f5b1c6db356b72cd655fdb5de30c45fc148d3d86016b4d4cb',
             0,
             'p2wpkh')
]


class Test_contr(unittest.TestCase):

    def setUp(self):
        self.btc_coin = coins.BitCoin(None)
        self.ltc_coin = coins.LiteCoin(None)
        seed = os.urandom(32)
        master_hd = hd.HDNode.make_master(
            seed, coin_network.BitcoinTestNetwork)
        self.btc_coin.make_hd_node(master_hd)
        self.ltc_coin.make_hd_node(master_hd)

    # @unittest.skip("TURN IT ON !!!!!!!!!!!!!!!!!!!!!")
    def test_impl(self):
        TO_SEND = 40000
        UTXO = UNSPENTS_SEGWIT
        SOURCE_BALANCE = sum(u.amount for u in UTXO)
        ##

        addr = self.btc_coin.make_address(key.AddressType.P2WPKH)
        log.debug(f"new address {addr}")

        addr.balance = SOURCE_BALANCE
        ctr = mutable_tx.MutableTransaction(addr, fee_manager.FeeManager())
        self.assertEqual(ctr.source_amount, addr.balance)
        self.assertGreaterEqual(ctr.change, 0)
        # fee
        confirm_minuntes = ctr.estimate_confirm_time()
        fee = ctr.fee
        log.warning(
            f"start fee => {ctr.fee} confirm minutes:{confirm_minuntes}")
        self.assertGreater(ctr.fee, 0)
        self.assertLess(confirm_minuntes, 30)
        self.assertGreaterEqual(ctr.change, 0)
        # fee change
        ctr.spb *= 0.5
        self.assertAlmostEqual(ctr.fee, fee * 0.5, 2)
        self.assertGreater(ctr.estimate_confirm_time(), confirm_minuntes)
        self.assertGreaterEqual(ctr.change, 0)
        #
        ctr.amount = TO_SEND
        ctr.substract_fee = False
        self.assertEqual(ctr.amount + ctr.fee + ctr.change, ctr.source_amount)
        ctr.substract_fee = True
        # we substrct fee from amount in prepare !!!!
        self.assertEqual(ctr.amount + ctr.change, ctr.source_amount)
        self.assertGreaterEqual(ctr.change, 0)

        # receiver validation
        btc_target = self.btc_coin.make_address(key.AddressType.P2WPKH)
        ltc_target = self.ltc_coin.make_address(key.AddressType.P2WPKH)

        # no receiver
        ctr.receiver = ""
        self.assertFalse(ctr.receiver_valid)
        with self.assertRaises(mutable_tx.WrongReceiver):
            ctr.prepare()

        # invalid receiver
        ctr.receiver = "h677909090f09f09"
        self.assertFalse(ctr.receiver_valid)
        with self.assertRaises(mutable_tx.WrongReceiver):
            ctr.prepare()

        # wrong coin receiver
        ctr.receiver = ltc_target.name
        self.assertFalse(ctr.receiver_valid)
        with self.assertRaises(mutable_tx.WrongReceiver):
            ctr.prepare()

        # no unspents
        ctr.receiver = btc_target.name
        self.assertTrue(ctr.receiver_valid)
        with self.assertRaises(mutable_tx.NewTxerror):
            ctr.prepare()
        ctr.address.unspents = UTXO
        ctr.substract_fee = False
        ctr.new_address_for_change = False
        self.assertGreaterEqual(ctr.change, 0)
        ctr.prepare()
        self.assertEqual(len(self.btc_coin), 2)
        ctr.substract_fee = True
        ctr.new_address_for_change = True
        self.assertGreaterEqual(ctr.change, 0)
        ctr.prepare()
        self.assertEqual(len(self.btc_coin), 3)

    def test_bindings(self):
        TO_SEND = 40000
        UTXO = UNSPENTS_SEGWIT
        SOURCE_BALANCE = sum(u.amount for u in UTXO)
        # btc
        def cast(m): return str(self.btc_coin.balance_human(m))
        # btc
        def fiat(m): return str(self.btc_coin.fiat_amount(m))
        # satoshi
        def parse(s): return int(self.btc_coin.from_human(s))
        ##
        gcd_ = gcd.GCD(True)  # pylint: disable=unused-variable
        address = self.btc_coin.make_address(key.AddressType.P2WPKH)
        address.balance = SOURCE_BALANCE
        txc = tx_controller.TxController(None, address)

        # test slot
        txc.balanceChanged.emit()

        #
        self.assertEqual(txc.balance, cast(SOURCE_BALANCE))
        self.assertEqual(txc.fiatBalance, fiat(SOURCE_BALANCE))
        # for a while
        self.assertEqual(txc.maxAmount, cast(SOURCE_BALANCE))

        #
        txc.amount = cast(TO_SEND)
        self.assertEqual(cast(TO_SEND), txc.amount)
        self.assertEqual(fiat(TO_SEND), txc.fiatAmount)

        # receiver
        btc_target = self.btc_coin.make_address(key.AddressType.P2WPKH)
        ltc_target = self.ltc_coin.make_address(key.AddressType.P2WPKH)

        txc.receiverAddress = ""
        self.assertFalse(txc.receiverValid)
        txc.receiverAddress = "989283982938928"
        self.assertFalse(txc.receiverValid)
        txc.receiverAddress = ltc_target.name
        self.assertFalse(txc.receiverValid)
        txc.receiverAddress = btc_target.name
        self.assertTrue(txc.receiverValid)

        # fee
        fee = parse(txc.feeAmount)
        log.info(f"spb factor:{txc.spbFactor} fee:{txc.feeAmount}")
        self.assertGreater(txc.spbFactor, 0)
        self.assertGreater(parse(txc.feeAmount), 0)
        txc.spbFactor = 1
        log.info(f"spb factor:{txc.spbFactor} fee:{txc.feeAmount}")
        self.assertGreater(parse(txc.feeAmount), fee)
        self.assertGreater(parse(txc.feeAmount), 0)
        txc.spbFactor = 0
        log.info(f"spb factor:{txc.spbFactor} fee:{txc.feeAmount}")
        self.assertLess(parse(txc.feeAmount), fee)
        self.assertGreater(parse(txc.feeAmount), 0)

        # change
        txc.spbFactor = 0
        self.assertEqual(txc.maxAmount, txc.balance)
        txc.substractFee = False
        self.assertEqual(parse(txc.balance), parse(
            txc.changeAmount) + parse(txc.amount) + parse(txc.feeAmount))
        txc.substractFee = True
        self.assertEqual(parse(txc.balance), parse(
            txc.changeAmount) + parse(txc.amount))
        change = parse(txc.changeAmount)
        # change fee
        txc.substractFee = False
        fee = parse(txc.feeAmount)
        txc.spbFactor = 0.5
        self.assertEqual(parse(txc.balance), parse(
            txc.changeAmount) + parse(txc.amount) + parse(txc.feeAmount))
        self.assertGreater(parse(txc.feeAmount), fee)
        self.assertLess(parse(txc.changeAmount), change)
        #
        txc.substractFee = True
        fee = parse(txc.feeAmount)
        txc.spbFactor = 1.
        self.assertEqual(parse(txc.balance), parse(
            txc.changeAmount) + parse(txc.amount))
        self.assertGreater(parse(txc.feeAmount), fee)
        # hard to get - but change remains the same !!!
        self.assertEqual(parse(txc.changeAmount), change)

    @unittest.skip("TODO: no segwit address detection")
    def test_legacy_address_validation(self):
        addr = self.btc_coin.make_address(key.AddressType.P2PKH)
        gcd_ = gcd.GCD(True)  # pylint: disable=unused-variable
        txc = tx_controller.TxController(None, addr)

        btc_target = self.btc_coin.make_address(key.AddressType.P2PKH)
        ltc_target = self.ltc_coin.make_address(key.AddressType.P2PKH)
        ltc_target_segwit = self.ltc_coin.make_address(key.AddressType.P2PKH)

        txc.receiverAddress = ltc_target.name
        self.assertFalse(txc.receiverValid)

        # TODO:
        txc.receiverAddress = ltc_target_segwit.name
        self.assertFalse(txc.receiverValid)

        txc.receiverAddress = btc_target.name
        self.assertTrue(txc.receiverValid)
