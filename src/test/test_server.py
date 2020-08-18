import unittest
from client.server import url_composer
from client.server import network_impl
import PySide2.QtCore as qt_core


class TestServer(unittest.TestCase):

    def test_url_composer(self):
        url = url_composer.UrlComposer(5)
        url.API_HOST = "_"
        self.assertEqual("_/v5/1", url.get_url("1"))
        self.assertEqual("_/v5/1/2/3", url.get_url("1", ["2", "3"]))
        gets = {
            "a": 4,
            "b": 5,
        }
        self.assertEqual("_/v5/1/2/3?a=4&b=5",
                         url.get_url("1", ["2", "3"], gets))

    def test_post(self):
        net = network_impl.NetworkImpl(None)
        data = b'{"data": {"type": "tx_broadcast", "attributes": {"data": "0100000003151818c1b80160277c897fff69391317177b93d12dd5c7afbbbc16ec8999d8da000000006b483045022100d41e9779739792d95b44cda90134a6e5be9dd5d2f142d5ce2f8500a0962d313d0220711ff2d2075f7de8925dbed040a5d89a7ba0e5a1125751a7d6175bd498fce9b40121021ecf14ab973e4b3dd631be9358317bfe9cd59863f2b6c1b1367c7e41b0ff2056ffffffff7a4256b23eaab97a7dddc77d2f8bce82c21d6ad31f062d73a10846cd9849fec0000000006b483045022025002174b954926dd4d7c831563e2a1a6251620eb7e8611cdefa8d04c1c1e905022100c36122d29131aa024e0888cc0204336cca415f03823bbca1106eb41c012492230121021ecf14ab973e4b3dd631be9358317bfe9cd59863f2b6c1b1367c7e41b0ff2056ffffffffe044255a03b78f991cd9f6c0894141d3c663747d543e9a302796003a9a8b8e0a010000006c4930460221008defc5030b44fc9109ecef342469839372f190f609fd213ace474c72309ffbc7022100be5a09b8dca52aef8067a6d684dc96579271863a51ac9113710f5bee00c881a50121021ecf14ab973e4b3dd631be9358317bfe9cd59863f2b6c1b1367c7e41b0ff2056ffffffff02204e000000000000160014086cc1ffcedf701acf633d88cb526891eb377a8705df020000000000160014e9f56ca09c01407ee34863e8f5c7467d10dd036200000000"}}}'
        app = qt_core.QCoreApplication()

        net._make_post_reply(
            "coins", ["btctest", "tx", "broadcast"], True, data, test=True)
        app.exec_()

    def test_row_post(self):
        import requests
        data = '{"data": {"type": "tx_broadcast", "attributes": {"data": "0100000003151818c1b80160277c897fff69391317177b93d12dd5c7afbbbc16ec8999d8da000000006b483045022100d41e9779739792d95b44cda90134a6e5be9dd5d2f142d5ce2f8500a0962d313d0220711ff2d2075f7de8925dbed040a5d89a7ba0e5a1125751a7d6175bd498fce9b40121021ecf14ab973e4b3dd631be9358317bfe9cd59863f2b6c1b1367c7e41b0ff2056ffffffff7a4256b23eaab97a7dddc77d2f8bce82c21d6ad31f062d73a10846cd9849fec0000000006b483045022025002174b954926dd4d7c831563e2a1a6251620eb7e8611cdefa8d04c1c1e905022100c36122d29131aa024e0888cc0204336cca415f03823bbca1106eb41c012492230121021ecf14ab973e4b3dd631be9358317bfe9cd59863f2b6c1b1367c7e41b0ff2056ffffffffe044255a03b78f991cd9f6c0894141d3c663747d543e9a302796003a9a8b8e0a010000006c4930460221008defc5030b44fc9109ecef342469839372f190f609fd213ace474c72309ffbc7022100be5a09b8dca52aef8067a6d684dc96579271863a51ac9113710f5bee00c881a50121021ecf14ab973e4b3dd631be9358317bfe9cd59863f2b6c1b1367c7e41b0ff2056ffffffff02204e000000000000160014086cc1ffcedf701acf633d88cb526891eb377a8705df020000000000160014e9f56ca09c01407ee34863e8f5c7467d10dd036200000000"}}}'

        resp = requests.post(
            "https://d1.bitmarket.network:30110/v1/coins/btctest/tx/broadcast",
            data=data,
            headers = {
                "Content-Type":"application/vnd.api+json"
            }
        )
        print( f"CODE->{resp.status_code} {resp.content}")
