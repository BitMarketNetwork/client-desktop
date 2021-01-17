
import logging
import os
import time
import unittest
from unittest.mock import patch, Mock
from typing import Iterable, Generator, Tuple, Optional

import bitcoinlib.transactions as btx

from bmnclient import gcd
from bmnclient.ui.gui import coin_manager, tx_controller
from bmnclient.wallet import coin_network, coins, fee_manager, hd, key, mutable_tx, address
from bmnclient.wallet import mtx_impl as mtx, tx

# from . import test_mtx


log = logging.getLogger(__name__)

SKIP_FILTER = False
SKIP_MTX = False

UNSPENTS_SEGWIT = [
    mtx.UTXO(1000000,
             1,
             '76a914905aa72f3d1747094a24d3adbc38905bb451ffc888ac',
             'f09c22717770fcd7e477953c3ca7ecb9bd44ec4d5392f24fdd247dbb8db2d388',
             0,
             'p2wpkh'),
    mtx.UTXO(2000000,
             1,
             # 'a9146015d175e191e6e5b99211e3ffc6ea7658cb051a87', !!!
             '0014905aa72f3d1747094a24d3adbc38905bb451ffc8',
             'f42c4ee1f95a3c9f5b1c6db356b72cd655fdb5de30c45fc148d3d86016b4d4cb',
             0,
             'p2wpkh')
]
UNSPENTS_SEGWIT_2 = [
    mtx.UTXO(1500000,
             1,
             '76a914905aa72f3d1747094a24d3adbc38905bb451ffc888ac',
             'f09c22717770fcd7e477953c3ca7ecb9bd44ec4d5392f24fdd247dbb8db2d388',
             0,
             'p2wpkh'),
    mtx.UTXO(2500000,
             1,
             # 'a9146015d175e191e6e5b99211e3ffc6ea7658cb051a87', !!!
             '0014905aa72f3d1747094a24d3adbc38905bb451ffc8',
             'f42c4ee1f95a3c9f5b1c6db356b72cd655fdb5de30c45fc148d3d86016b4d4cb',
             0,
             'p2wpkh')]

UNSPENTS_SEGWIT_3 = [
    mtx.UTXO(500000,
             1,
             '76a914905aa72f3d1747094a24d3adbc38905bb451ffc888ac',
             'f09c22717770fcd7e477953c3ca7ecb9bd44ec4d5392f24fdd247dbb8db2d388',
             0,
             'p2wpkh'),
    mtx.UTXO(200000,
             1,
             # 'a9146015d175e191e6e5b99211e3ffc6ea7658cb051a87', !!!
             '0014905aa72f3d1747094a24d3adbc38905bb451ffc8',
             'f42c4ee1f95a3c9f5b1c6db356b72cd655fdb5de30c45fc148d3d86016b4d4cb',
             0,
             'p2wpkh'),
    mtx.UTXO(800000,
             1,
             # 'a9146015d175e191e6e5b99211e3ffc6ea7658cb051a87', !!!
             '0014905aa72f3d1747094a24d3adbc38905bb451ffc8',
             'f42c4ee1f95a3c9f5b1c6db356b72cd655fdb5de30c45fc148d3d86016b4d4cb',
             0,
             'p2wpkh')]

UNSPENTS = [
    mtx.UTXO(83727960,
             15,
             '76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac',
             'f3ad23dac2a3546167b27a43ac3e370236caf93f75bfcf27c625ec839d397888',
             1),
    mtx.UTXO(30004444,
             15,
             '76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac',
             'f3ad23dac2a3546167b27a43ac3e370236caf93f75bfcf27c625ec839d397888',
             1)
]
UNSPENTS_2 = [
    mtx.UTXO(83727960,
             15,
             '76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac',
             'f3ad23dac2a3546167b27a43ac3e370236caf93f75bfcf27c625ec839d397888',
             1),
    mtx.UTXO(30004444,
             15,
             '76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac',
             'f3ad23dac2a3546167b27a43ac3e370236caf93f75bfcf27c625ec839d397888',
             1)
]


class ParseMixin:
    def _setup(self):
        self.btc_coin = coins.Bitcoin(None)
        self.ltc_coin = coins.Litecoin(None)
        seed = os.urandom(32)
        master_hd = hd.HDNode.make_master(
            seed, coin_network.BitcoinTestNetwork)
        self.btc_coin.make_hd_node(master_hd)
        self.ltc_coin.make_hd_node(master_hd)

    def cast(self, m):
        return str(self.btc_coin.balance_human(m))

    def fiat(self, m):
        return str(self.btc_coin.fiat_amount(m))

    def parse(self, m):
        return int(self.btc_coin.from_human(m) + 0.5)


class TestContr(unittest.TestCase, ParseMixin):

    def setUp(self):
        self._setup()

    # @unittest.skip("TURN IT ON !!!!!!!!!!!!!!!!!!!!!")
    def test_impl(self):
        TO_SEND = 40000
        UTXO = UNSPENTS_SEGWIT
        ##

        addr = self.btc_coin.make_address(key.AddressType.P2WPKH)
        self.assertEqual(len(self.btc_coin), 1)
        addr.unspents = UTXO
        log.debug(f"new address {addr}")

        ctr = mutable_tx.MutableTransaction(addr, fee_manager.FeeManager())
        ctr.use_coin_balance = False
        ctr.set_max()
        self.assertEqual(ctr.source_amount, addr.balance)
        self.assertGreaterEqual(
            ctr.change, 0, f"mtx amount:{ctr.amount} src:{addr.balance}")
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
        self.assertEqual(ctr.amount + ctr.fee +
                         ctr.change, ctr.filtered_amount)
        ctr.substract_fee = True
        # we substrct fee from amount in prepare !!!!
        self.assertEqual(ctr.amount + ctr.change, ctr.filtered_amount)
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
        ctr.receiver = "bc1"
        self.assertFalse(ctr.receiver_valid)
        with self.assertRaises(mutable_tx.WrongReceiver):
            ctr.prepare()

        # wrong coin receiver
        ctr.receiver = ltc_target.name
        self.assertFalse(ctr.receiver_valid)
        with self.assertRaises(mutable_tx.WrongReceiver):
            ctr.prepare()

        ctr.receiver = btc_target.name
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
        self.assertEqual(len(ctr.mtx.TxIn), 1)
        ctr.cancel()
        self.assertEqual(len(self.btc_coin), 2)

    def test_bindings(self):
        TO_SEND = 400000
        SOURCE_BALANCE = sum(u.amount for u in UNSPENTS_SEGWIT)
        ##
        gcd_ = gcd.GCD(True)  # pylint: disable=unused-variable
        address = self.btc_coin.make_address(key.AddressType.P2WPKH)
        address.unspents = UNSPENTS_SEGWIT
        txc = tx_controller.TxController(None, address)

        # test slot
        txc.maxAmountChanged.emit()

        #
        self.assertEqual(txc.maxAmount, self.cast(SOURCE_BALANCE))
        self.assertEqual(txc.fiatBalance, self.fiat(SOURCE_BALANCE))
        # for a while
        self.assertEqual(txc.maxAmount, self.cast(SOURCE_BALANCE))

        #
        txc.amount = self.cast(TO_SEND)
        self.assertEqual(self.cast(TO_SEND), txc.amount)
        self.assertEqual(self.fiat(TO_SEND), txc.fiatAmount)

        # receiver
        btc_target = self.btc_coin.make_address(key.AddressType.P2WPKH)
        ltc_target = self.ltc_coin.make_address(key.AddressType.P2WPKH)
        # !!!
        self.assertEqual(self.cast(TO_SEND), txc.amount)

        txc.receiverAddress = ""
        self.assertFalse(txc.receiverValid)
        txc.receiverAddress = "989283982938928"
        self.assertFalse(txc.receiverValid)
        txc.receiverAddress = ltc_target.name
        self.assertFalse(txc.receiverValid)
        txc.receiverAddress = btc_target.name
        self.assertTrue(txc.receiverValid)

        self.assertTrue(txc.canSend)

        # fee
        fee = self.parse(txc.feeAmount)
        log.info(f"spb factor:{txc.spbFactor} fee:{txc.feeAmount}")
        self.assertGreater(txc.spbFactor, 0)
        self.assertGreater(self.parse(txc.feeAmount), 0)
        txc.spbFactor = 1
        log.info(f"spb factor:{txc.spbFactor} fee:{txc.feeAmount}")
        self.assertTrue(txc.canSend)
        self.assertGreater(self.parse(txc.feeAmount), fee)
        self.assertGreater(self.parse(txc.feeAmount), 0)
        txc.spbFactor = 0
        log.info(f"spb factor:{txc.spbFactor} fee:{txc.feeAmount}")
        self.assertTrue(txc.canSend)
        self.assertLess(self.parse(txc.feeAmount), fee)
        self.assertGreater(self.parse(txc.feeAmount), 0)

        # change
        txc.substractFee = False
        self.assertTrue(txc.canSend)
        self.assertEqual(self.parse(txc.filteredAmount), self.parse(
            txc.changeAmount) + self.parse(txc.amount) + self.parse(txc.feeAmount))
        txc.substractFee = True
        self.assertTrue(txc.canSend)
        self.assertEqual(self.parse(txc.filteredAmount), self.parse(
            txc.changeAmount) + self.parse(txc.amount), f"ch:{txc.changeAmount} am:{txc.amount}")
        change = self.parse(txc.changeAmount)
        # change fee
        txc.substractFee = False
        fee = self.parse(txc.feeAmount)
        txc.spbFactor = 0.5
        self.assertTrue(txc.canSend)
        self.assertEqual(self.parse(txc.filteredAmount), self.parse(
            txc.changeAmount) + self.parse(txc.amount) + self.parse(txc.feeAmount))
        self.assertGreater(self.parse(txc.feeAmount), fee)
        self.assertLess(self.parse(txc.changeAmount), change)
        #
        txc.substractFee = True
        fee = self.parse(txc.feeAmount)
        txc.spbFactor = 1.
        self.assertTrue(txc.canSend)
        self.assertEqual(self.parse(txc.filteredAmount), self.parse(
            txc.changeAmount) + self.parse(txc.amount))
        self.assertGreater(self.parse(txc.feeAmount), fee)
        # hard to get - but change remains the same !!!
        self.assertEqual(self.parse(txc.changeAmount), change)

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


class TestContr2(unittest.TestCase, ParseMixin):

    def setUp(self):
        super()._setup()
        self.addr = self.btc_coin.make_address(key.AddressType.P2PKH)
        self.addr.unspents = UNSPENTS_SEGWIT_3
        self.addr2 = self.btc_coin.make_address(key.AddressType.P2PKH)
        self.addr2.unspents = UNSPENTS_SEGWIT_2
        self.addr3 = self.btc_coin.make_address(key.AddressType.P2PKH)
        self.addr3.unspents = UNSPENTS_SEGWIT
        self.gcd_ = gcd.GCD(True)  # pylint: disable=unused-variable
        self.txc = tx_controller.TxController(None, self.addr)
        self.txc.receiverAddress = self.btc_coin.name

    def tearDown(self):
        self.btc_coin.clear()
        self.assertEqual(len(self.btc_coin), 0)
        self.ltc_coin.clear()
        self.assertEqual(len(self.ltc_coin), 0)

    def test_valid(self):
        ##
        NUMBER = 20
        self.txc.use_hint = False

        def check(i):
            am = self.parse(self.txc.maxAmount) / NUMBER * i
            with self.subTest(f"{i}: am:{am}  address only:{not self.txc.useCoinBalance}"):
                self.txc.amount = self.cast(am)
                self.assertEqual(self.txc.wrongAmount, 0 == i or i >=
                                 NUMBER, f"max:{self.parse(self.txc.maxAmount)}")
                if not self.txc.wrongAmount:
                    self.assertEqual(
                        self.parse(self.txc.changeAmount) +
                        self.parse(self.txc.amount) +
                        self.parse(self.txc.feeAmount),
                        self.txc.impl.filtered_amount
                    )
                    log.warning(
                        f"@@@@@@@@@@@@@@@ am:{am} ch:{self.txc.changeAmount}")
                    self.assertEqual(self.txc.hasChange, True)
                    #  self.txc.impl.change >= 0)
        for i in range(NUMBER + 2):
            self.txc.useCoinBalance = False
            check(i)
            self.txc.useCoinBalance = True
            check(i)

    def test_guess_amount(self):
        AMOUNT = 400000
        self.txc.amount = self.cast(AMOUNT)
        self.txc.useCoinBalance = True
        self.assertTrue(self.txc.canSend and not self.txc.wrongAmount)
        self.txc.useCoinBalance = False
        self.assertTrue(self.txc.canSend and not self.txc.wrongAmount)
        self.txc.amount = self.cast(self.parse(self.txc.maxAmount) * 2)
        self.assertTrue(not self.txc.canSend and self.txc.wrongAmount)

    def test_amount(self):
        UTXO = UNSPENTS_SEGWIT
        SOURCE_BALANCE = sum(u.amount for u in UTXO)
        address = self.btc_coin.make_address(key.AddressType.P2WPKH)
        address.balance = SOURCE_BALANCE
        assert address
        gcd_ = gcd.GCD(True)  # pylint: disable=unused-variable
        txc = tx_controller.TxController(None, address)

        def test_value(val: str):
            txc.amount = val
            self.assertEqual(val, txc.amount)
        test_value("0.44")
        test_value("0.00")
        test_value("0.100")


@unittest.skipIf(SKIP_FILTER, reason="Local filter settings")
class Test_source_list(unittest.TestCase):

    def setUp(self):
        self.start_time = time.time()

    def tearDown(self):
        t = time.time() - self.start_time
        log.info(f"Total {self.id()} duration: {t*1e3:.3} ms")

    def test_select(self):

        def filter(sources: Iterable[int], amount: int, desired_amount: int = 0, count: Optional[int] = None) -> Tuple[list, int]:
            start = time.time()
            src, am = mutable_tx.MutableTransaction.select_sources(
                sources, amount, lambda a: a)
            t = time.time() - start
            if isinstance(desired_amount, bool):
                if desired_amount:
                    self.assertGreaterEqual(am, amount)
                else:
                    self.assertFalse(src)
            else:
                self.assertEqual(desired_amount or amount, am)
            if count:
                self.assertEqual(count, len(src))
            log.warning(
                f"for target:{amount} and sources:{sources} found {am} with:{src} duration: {t*1e4:.4} ms")

        filter([5], 1, 5, count=1)  # !!
        filter([1] * 10 + [10], 10, count=10)
        filter([1] * 10 + [10], 9, count=9)
        filter([2] * 10 + [20], 19, 20, count=10)  # !!
        filter([20, 40, 100, 3000, 10000], 14500, False)
        filter([20, 40, 100, 3000, 2000, 10000, 20000], 14500, True)
        filter([20, 40, 60, 100, 3000, 2000, 10000, 20000], 12200, True)
        filter([20, 100, 1], 20)
        filter([20, 100, 1], 100)
        filter([20, 100, 1], 70, 100)
        filter([20, 100, 1], 10, 20)
        filter([20, 100, 1], 1)
        filter([20, 100, 1, 1, 2], 122, count=4)
        filter([20, 100, 1], 21)
        filter([20, 40, 100, 1], 110, 120)
        filter([20, 40, 100, 1], 1000, 161)


@unittest.skipIf(SKIP_MTX, reason="Local filter settings")
class TestResultMtx(unittest.TestCase, ParseMixin):

    def setUp(self):
        self._setup()
        self.addr = self.btc_coin.make_address(key.AddressType.P2PKH)
        self.addr_1 = self.btc_coin.make_address(key.AddressType.P2WPKH)
        self.gcd_ = gcd.GCD(True)
        self.target = self.btc_coin.make_address(key.AddressType.P2PKH)

    def __check_mtx(self, segwit: bool):
        self.assertTrue(self.txc.prepareSend())
        impl = self.txc.impl
        raw = impl.mtx
        # amounts
        self.assertEqual(raw.in_amount, impl.filtered_amount)
        self.assertEqual(raw.out_amount, impl.amount + impl.change)
        self.assertEqual(raw.fee, impl.fee)
        # outputs
        outs = raw.TxOut
        out_adds = [o.address for o in outs]
        # self.assertEqual(len(out_adds), len(set(out_adds)) , out_adds)
        self.assertEqual(len(outs), 2)
        self.assertIn(self.target.name, out_adds)
        self.assertNotIn(self.addr.name, out_adds)
        # inputs
        ins = raw.TxIn
        ins_adds = [o.address.name for o in ins]
        ins_wit = [o.witness for o in ins]
        ins_scr = [o.script_sig for o in ins]
        self.assertNotIn(self.target.name, ins_adds)
        if not self.txc.useCoinBalance:
            self.assertIn(self.addr.name, ins_adds)
        self.assertEqual(all(ins_wit), segwit, ins_wit)
        self.assertEqual(all(ins_scr), not segwit, ins_wit)
        ##
        # self.assertEqual(len(ins_adds), len(set(ins_adds)), ins_adds)
        # external test
        extx = btx.Transaction.import_raw(raw.to_hex())
        self.assertEqual(extx.witness_type, 'segwit' if segwit else 'legacy')
        extx.info()

    def __test(self, segwit: bool):
        ###
        NUMBER = 5
        self.txc = tx_controller.TxController(None, self.addr)
        self.txc.receiverAddress = self.target.name
        self.txc.newAddressForChange = True

        def check(i):
            am = self.parse(self.txc.maxAmount) / NUMBER * i
            with self.subTest(f"{i}: am:{am}  address only:{not self.txc.useCoinBalance}"):
                self.txc.amount = self.cast(am)
                self.__check_mtx(segwit)

        for i in range(1, NUMBER):
            self.txc.useCoinBalance = False
            check(i)
            self.txc.useCoinBalance = True
            check(i)

    def test_segwit(self):
        self.addr.unspents = UNSPENTS_SEGWIT_3
        self.addr_1.unspents = UNSPENTS_SEGWIT_2
        self.__test(True)

    def test_legacy(self):
        self.addr.unspents = UNSPENTS
        self.addr_1.unspents = UNSPENTS_2
        self.__test(False)


class MockFee:
    max_spb = 100


class MockSignal:
    counter = 0

    def __init__(self, case=None):
        self.case = case

    def emit(self, *args):
        self.__class__.counter += 1


class BroadcastSignal(MockSignal):
    ok = True

    def emit(self, mtx):
        super().emit()
        self.case.assertEqual(self.case.txc.impl, mtx)
        if self.ok:
            mtx.send_callback(True)
        else:
            mtx.send_callback(False, "error")


class MempoolSignal(MockSignal):
    coin = None

    def emit(self, coin):
        super().emit()
        self.__class__.coin = coin


class SentSignal(MockSignal):
    pass


class FailureSignal(MockSignal):
    pass


class MockGcd(MockSignal):

    @classmethod
    def get_instance(cls):
        me = cls()
        me.fee_man = MockFee()
        me.broadcastMtx = BroadcastSignal(cls.case)
        me.mempoolCoin = MempoolSignal(cls.case)
        return me


class TestSend(unittest.TestCase, ParseMixin):

    def setUp(self):
        self._setup()
        self.addr = self.btc_coin.make_address(key.AddressType.P2PKH)
        self.addr_1 = self.btc_coin.make_address(key.AddressType.P2PKH)
        self.target = self.btc_coin.make_address(key.AddressType.P2PKH)
        self.addr.unspents = UNSPENTS_SEGWIT_3
        self.addr_1.unspents = UNSPENTS_SEGWIT_2
        MockGcd.case = self

    @patch("client.ui.gui.tx_controller.gcd.GCD", new=MockGcd)
    def test_callback(self):
        tx_controller.TxController.sent = SentSignal(self)
        tx_controller.TxController.fail = FailureSignal(self)
        self.txc = tx_controller.TxController(None, self.addr)
        self.txc.receiverAddress = self.target.name
        self.txc.amount = self.cast(self.parse(self.txc.maxAmount) * 0.8)
        self.assertTrue(self.txc.prepareSend())
        self.txc.send()
        #
        self.assertEqual(MempoolSignal.counter, 1)
        self.assertEqual(FailureSignal.counter, 0)
        self.assertEqual(BroadcastSignal.counter, 1)
        self.assertEqual(SentSignal.counter, 1)
        self.assertIn(self.addr, MempoolSignal.coin)
        self.assertIn(self.target, MempoolSignal.coin)
        # test dummy ui tx
        utx = self.txc.impl.ui_tx
        self.assertIsNotNone(utx)
        self.assertIsInstance(utx, tx.Transaction)
        out_addr = [out.address for out in utx.outputs]
        self.assertIn(self.target.name, out_addr)
        self.assertIn(self.txc.changeAddress, out_addr)
        inp_addr = [inp.address for inp in utx.inputs]
        self.assertIn(self.addr.name, inp_addr)
        self.assertIn(self.addr_1.name, inp_addr)

        BroadcastSignal.ok = False
        self.txc.send()
        self.assertEqual(FailureSignal.counter, 1)
        self.assertEqual(BroadcastSignal.counter, 2)
