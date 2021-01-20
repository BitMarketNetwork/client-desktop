
import unittest
from unittest import skip

import PySide2.QtCore as qt_core

from bmnclient import gcd, loading_level
from bmnclient.ui import gui
from bmnclient.server import net_cmd, network_impl


"""
This sequence of testcase are supposed to cover network commands functionality
It is supposed to be more behavior testing
"""


class TestNetworkCommands(unittest.TestCase):

    def test_tx_history(self):
        gcd_ = gcd.GCD()
        root = gui.Application(gcd_)
        # app = qt_core.QCoreApplication()
        root.app.processEvents()
        ##

        coin = gcd_.btc_coin
        wallet = coin.append_address("1A8JiWcwvpY7tAopUkSnGuEYHmzGYfZPiq")

        net_cmd.AddressHistoryCommand.verbose = True
        network_impl.NetworkImpl.CMD_DELAY = 500

        root.app.processEvents()
        def delayed_call():
            gcd_.addressHistory.emit(wallet)
            gcd_.startNetwork.emit()
            """
            TODO: cover main thread is untouched
            """
        qt_core.QTimer.singleShot(500, delayed_call)
        root.app.exec_()
