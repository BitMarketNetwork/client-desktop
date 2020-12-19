

import logging
import unittest
from unittest import skip

import PySide2.QtCore as qt_core
from bmnclient import gcd
from bmnclient.server import net_cmd, network_impl
from bmnclient.ui import gui

log = logging.getLogger(__name__)
"""
Test for network commands' queue
"""

@skip
class TestQueue(unittest.TestCase):

    def setUp(self):
        gcd_ = gcd.GCD(silent_mode=True)
        self.net = network_impl.NetworkImpl(gcd_)
        coin = gcd_.btc_coin
        self.wallet = coin.append_address("1A8JiWcwvpY7tAopUkSnGuEYHmzGYfZPiq")

    def test_empty(self):
        "importtant case"
        cmd = net_cmd.AddressHistoryCommand(self.wallet)
        self.net._push_cmd(cmd)
        self.assertEqual(len(self.net._queue), 1)

    def test_unique(self):
        cmd1 = net_cmd.UpdateCoinsInfoCommand(True)
        cmd2 = net_cmd.UpdateCoinsInfoCommand(True)
        self.net._push_cmd(net_cmd.AddressHistoryCommand(self.wallet))
        self.assertEqual(len(self.net._queue), 1)
        self.net._push_cmd(cmd1)
        self.assertEqual(len(self.net._queue), 2)
        self.net._push_cmd(cmd2)
        self.assertEqual(len(self.net._queue), 2)
        self.net._push_cmd(net_cmd.AddressHistoryCommand(self.wallet))
        self.assertEqual(len(self.net._queue), 3)

    def test_priority(self):
        cmds = [net_cmd.AddressInfoCommand(self.wallet, low_priority=True), net_cmd.AddressHistoryCommand(self.wallet), net_cmd.AddressInfoCommand(
            self.wallet, high_priority=True), net_cmd.AddressInfoCommand(self.wallet, low_priority=True), net_cmd.AddressInfoCommand(self.wallet, high_priority=True), net_cmd.AddressHistoryCommand(self.wallet)]

        [self.net._push_cmd(cmd) for cmd in cmds]

        self.assertEqual(len(self.net._queue), len(cmds))
        self.assertTrue(self.net._queue[0].high_priority)
        self.assertTrue(self.net._queue[1].high_priority)
        self.assertTrue(self.net._queue[-1].low_priority)
        self.assertTrue(self.net._queue[-2].low_priority)

    def test_priority_force(self):
        self.assertFalse(self.net.busy)
        self.assertFalse(self.net._queue)
        cmd1 = net_cmd.UpdateCoinsInfoCommand(True)
        self.net._push_cmd(cmd1)
        self.assertTrue(self.net.busy)
        cmd2 = net_cmd.UpdateCoinsInfoCommand(True)
        self.net._push_cmd(cmd1)
        # normal push
        cmd3 = net_cmd.AddressHistoryCommand(self.wallet)
        self.net._push_cmd(cmd3)
        self.assertEqual(len(self.net._queue), 2)
        self.assertIsInstance(
            self.net._queue[0], net_cmd.UpdateCoinsInfoCommand)
        # force push
        cmd4 = net_cmd.AddressInfoCommand(self.wallet)
        self.net._push_cmd(cmd4, True)
        self.assertIsInstance(self.net._queue[0], net_cmd.AddressInfoCommand)


class TestRequest(unittest.TestCase):
    app_ = ApplicationBase(qt_core.QCoreApplication)

    def setUp(self):
        gcd_ = gcd.GCD(silent_mode=True)
        gcd_.app = gui.Application(gcd_, self.app_)
        self.net = network_impl.NetworkImpl(gcd_)
        coin = gcd_.btc_coin
        self.wallet = coin.append_address("1A8JiWcwvpY7tAopUkSnGuEYHmzGYfZPiq")

    def tearDown(self):
        pass
        # self.root.clear()

    def test_launch(self):
        self.assertFalse(self.net.busy)
        cmd1 = net_cmd.UpdateCoinsInfoCommand(True)
        result = self.net._run_cmd(cmd1)
        self.assertTrue(result)
        log.debug(result)
        # TODO: NOT COMPLETED !!! Validate req priority and another stuff
