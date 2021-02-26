
import json
import logging
from datetime import datetime
from typing import Union

from .. import loading_level
from . import net_cmd

log = logging.getLogger(__name__)


class DummyCommandBase:

    def feed_data(self, data: Union[dict, str]):

        if isinstance(data, dict):
            data = {
                'data': {
                    'attributes': data,
                },
                'meta': {
                    'timeframe': 1,
                }
            }
            self.onResponseData(json.dumps(data).encode())
        else:
            self.onResponseData(data.encode())
            raise NotImplementedError
        self.statusCode = 200
        return self.onResponseFinished()

    def run(self):
        pass


class IncomingTransferCommand(net_cmd.AddressHistoryCommand, DummyCommandBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect_()

    def run(self):
        """
         {'type': 'p2wpkh', 'address': 'ltc1qwj0yzstqea3ht0003yys2f8xztmx094nnehy29', 'tx_list':
         {'2fe83142f7537155ac0b6eee376070e933f27f28d470af44a1f522792832d809':
         {'height': 1855731, 'time': 1591599231, 'time_human': '2020-06-08T06:53:51Z', 'amount': 100000000, 'amount_human': '1', 'fee': 8777, 'fee_human': '0.00008777', 'coinbase': 0,
          'input': [{'output_type': 'witness_v0_keyhash', 'type': 'p2wpkh', 'address': 'ltc1q33rf3mvx6t0eatqu7pmxxc7xpnj5hjdxejgsfg', 'amount': 100000000, 'amount_human': '1'}],
           'output': [{'output_type': 'witness_v0_keyhash', 'type': 'p2wpkh', 'address': 'ltc1qwj0yzstqea3ht0003yys2f8xztmx094nnehy29', 'amount': 10000000, 'amount_human': '0.1'},
         {'output_type': 'witness_v0_keyhash', 'type': 'p2wpkh', 'address': 'ltc1qwrcg4rhyevd8w75surrrsq8nxlsp80y4q2xtn0',
         'amount': 89991223, 'amount_human': '0.89991223'}]}}, 'first_offset': '1856349.0', 'last_offset': None}
        """
        table = {
            'address': self._wallet.name,
            'tx_list': {
                '2fe83142f7537155ac0b6eee376070e933f27f28d470af44a1f522792832d8000': {
                    'height': self._wallet.coin.height,
                    'time': datetime.now().timestamp(),
                    'amount': 10000000,
                    'fee': 300,
                    'coinbase': 0,
                    'input': [],
                    'output': [
                        {
                            'type': 'p2wpkh',
                            'address': self._wallet.name,
                            'amount': 10000000,
                        }
                    ],
                }
            },
            'first_offset': '1764128.0',
            'last_offset': None,
        }
        self.feed_data(table)

    def clone(self, first_offset=None, forth=True):
        return None


class UndoTransactionCommand(net_cmd.BaseNetworkCommand):
    _METHOD = net_cmd.HttpMethod.POST
    action = "coins"
    level = loading_level.LoadingLevel.NONE

    def __init__(self, coin, count: int, parent):
        super().__init__(parent=parent)
        self._coin = coin
        self._count = count

    @property
    def args(self):
        return [self._coin.name, "undo"]

    @property
    def args_get(self):
        return {
            "coin": self._count,
        }

    def onResponseFinished(self) -> None:
        pass
