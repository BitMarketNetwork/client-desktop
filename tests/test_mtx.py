from __future__ import annotations

import logging
from os import urandom
from random import shuffle
from typing import TYPE_CHECKING
from unittest import TestCase

from bmnclient.coins.coin_bitcoin import Bitcoin
from bmnclient.coins.hd import HdNode

if TYPE_CHECKING:
    from typing import List, Sequence
    from bmnclient.coins.abstract.coin import AbstractCoin

log = logging.getLogger(__name__)


class TestSelectUtxo(TestCase):
    def setUp(self) -> None:
        self._coin = Bitcoin()
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)
        self.assertTrue(self._coin.deriveHdNode(root_node))

    def _createUtxoList(
            self,
            address: Bitcoin.Address,
            amount_list: Sequence[int]) -> None:
        utxo_list: List[Bitcoin.Tx.Utxo] = []
        for i in range(len(amount_list)):
            utxo_list.append(Bitcoin.Tx.Utxo(
                self._coin,
                name=i.to_bytes(32, "big").hex(),
                height=100 + i,
                index=0,
                amount=amount_list[i]))
        address.utxoList = utxo_list

    @classmethod
    def _isLowHeightUtxo(
            cls,
            utxo_list: List[Bitcoin.Tx.Utxo],
            utxo):
        result = False
        for far_utxo in utxo_list:
            if far_utxo.amount == utxo.amount:
                if far_utxo is not utxo and far_utxo.height > utxo.height:
                    result = True
        return result

    def test_find_ideal_utxo(self) -> None:
        address = self._coin.deriveHdAddress(account=0, is_change=False)
        self.assertIsNotNone(address)

        # no utxo
        for r in range(100):
            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, r)
            self.assertIsNone(utxo)

        # single utxo with amount 0, 1
        if True:
            for amount in (0, 1):
                self._createUtxoList(address, (amount, ))
                # noinspection PyProtectedMember
                utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 0)
                if not amount:
                    self.assertIsNotNone(utxo)
                    self.assertEqual(amount, utxo.amount)
                else:
                    self.assertIsNone(utxo)

                # noinspection PyProtectedMember
                utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 1)
                if not amount:
                    self.assertIsNone(utxo)
                else:
                    self.assertIsNotNone(utxo)
                    self.assertEqual(amount, utxo.amount)

                # noinspection PyProtectedMember
                utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 2)
                self.assertIsNone(utxo)

        # multiple utxo
        if True:
            self._createUtxoList(address, (0, 1, 2, 3, 4, 5, 6, 6))

            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 7)
            self.assertIsNone(utxo)

            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 6)
            self.assertIsNotNone(utxo)
            self.assertEqual(6, utxo.amount)
            self.assertTrue(self._isLowHeightUtxo(address.utxoList, utxo))

            # noinspection PyProtectedMember
            utxo = self._coin.TxFactory._findExactUtxo(address.utxoList, 4)
            self.assertIsNotNone(utxo)
            self.assertEqual(4, utxo.amount)

    def test_find_single_address_single_utxo(self) -> None:
        address = self._coin.deriveHdAddress(account=0, is_change=False)
        self.assertIsNotNone(address)

        # find same amount
        if True:
            amount_list = [x for x in range(1000)]
            shuffle(amount_list)
            self._createUtxoList(address, amount_list)
            self.assertEqual(1000, len(address.utxoList))
            for i in range(len(address.utxoList)):
                # noinspection PyProtectedMember
                l, a = self._coin.TxFactory._findOptimalUtxoList(
                    address.utxoList,
                    i)
                self.assertEqual(1, len(l))
                self.assertEqual(i, a)

        # find nearest amount + height test
        if True:
            amount_list = list(range(1, 1000, 2)) + list(range(1, 1000, 2))
            shuffle(amount_list)
            self._createUtxoList(address, amount_list)
            self.assertEqual(500 * 2, len(address.utxoList))
            for i in range(0, 1000, 2):
                # noinspection PyProtectedMember
                l, a = self._coin.TxFactory._findOptimalUtxoList(
                    address.utxoList,
                    i)
                self.assertEqual(1, len(l))
                self.assertEqual(i + 1, a)
                self.assertTrue(self._isLowHeightUtxo(address.utxoList, l[0]))

    def test_find_single_address_multiple_utxo(self) -> None:
        address = self._coin.deriveHdAddress(account=0, is_change=False)
        self.assertIsNotNone(address)

        amount_list = list(range(0, 10)) * 4
        shuffle(amount_list)
        self._createUtxoList(address, amount_list)
        self.assertEqual(40, len(address.utxoList))

        test_list = (
            (9, 9, 1),
            (10, 10, 2),
            (21, 21, 3),
            (28, 28, 4),
            (29, 29, 4),
            (100, 102, 13),
            (200, 0, 0),
        )

        for (amount, result_amount, utxo_count) in test_list:
            # noinspection PyProtectedMember
            l, a = self._coin.TxFactory._findOptimalUtxoList(
                address.utxoList,
                amount)
            self.assertEqual(utxo_count, len(l))
            self.assertEqual(result_amount, a)

        amount_list = list(range(1, 10))
        shuffle(amount_list)
        self._createUtxoList(address, amount_list)
        self.assertEqual(9, len(address.utxoList))

        test_list = (
            (9, 9, 1),
            (10, 11, 2),
            (20, 21, 3),
            (45, 45, 9),
        )

        for (amount, result_amount, utxo_count) in test_list:
            # noinspection PyProtectedMember
            l, a = self._coin.TxFactory._findOptimalUtxoList(
                address.utxoList,
                amount)
            self.assertEqual(utxo_count, len(l))
            self.assertEqual(result_amount, a)


class TestMutableTx(TestCase):
    def setUp(self) -> None:
        self._coin = Bitcoin()
        root_node = HdNode.deriveRootNode(urandom(64))
        self.assertIsNotNone(root_node)
        self.assertTrue(self._coin.deriveHdNode(root_node))

    def _createInput(
            self,
            coin: AbstractCoin,
            *,
            name: str,
            index: int,
            private_key: str,
            address_type: AbstractCoin.Address.Type,
            script_type: AbstractCoin.Script.Type,
            amount: int,
            sequence: int) -> AbstractCoin.TxFactory.MutableTx.Input:
        private_key = coin.Address.importKey(coin, private_key)
        self.assertIsNotNone(private_key)

        address = coin.Address.createAddress(
            self._coin,
            type_=address_type,
            key=private_key)
        self.assertIsNotNone(address)

        utxo = coin.Tx.Utxo(
            coin,
            name=bytes.fromhex(name)[::-1].hex(),
            height=1,
            index=index,
            amount=amount,
            script_type=script_type)
        utxo.address = address
        return coin.TxFactory.MutableTx.Input(utxo, sequence=sequence)

    @classmethod
    def _createOutput(
            cls,
            coin: AbstractCoin,
            *,
            address_name: str,
            address_type: AbstractCoin.Address.Type,
            amount: int) -> AbstractCoin.TxFactory.MutableTx.Output:
        address = coin.Address(
            coin,
            name=address_name,
            type_=address_type)
        return coin.TxFactory.MutableTx.Output(address, amount)

    def test_p2pkh(self) -> None:
        input_list = [
            self._createInput(
                self._coin,
                name="8878399d83ec25c627cfbf753ff9ca3602373eac437ab2676154a3c2da23adf3", # noqa
                index=1,
                private_key="L3jsepcttyuJK3HKezD4qqRKGtwc8d2d1Nw6vsoPDX9cMcUxqqMv", # noqa
                # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                script_type=self._coin.Script.Type.P2PKH,
                amount=83727960,
                sequence=0xfffffffe),
        ]
        output_list = [
            self._createOutput(
                self._coin,
                address_name="1N8QYQNAD8PLEJjmCGGR8iN1iuR9yXtY1x",  # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                amount=50000
            ),
            self._createOutput(
                self._coin,
                address_name="1ELReFsTCUY2mfaDTy32qxYiT49z786eFg",  # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                amount=83658760
            )
        ]
        mtx = self._coin.TxFactory.MutableTx(
            self._coin,
            input_list,
            output_list)
        self.assertTrue(mtx.sign())
        self.assertEqual(
            "b8eab75158fc3f3bd8479005a02eef5a13c5d80e364ab155a4ebdb19d418b331",  # noqa
            mtx.name)
        self.assertEqual(
            "01000000018878399d83ec25c627cfbf753ff9ca3602373eac437ab2676154a3c2"  # noqa
            "da23adf3010000006b483045022100b167dd5c560454a8c7e6425aebde64723311"  # noqa
            "0158acf84b1b81a9ed98b2c613a20220551d562999009596a0c1c12b2a77861cc9"  # noqa
            "150bc77c025ed5309ff77d39bc889f0121033d5c2875c9bd116875a71a5db64cff"  # noqa
            "cb13396b163d039b1d9327824891804334feffffff0250c30000000000001976a9"  # noqa
            "14e7c1345fc8f87c68170b3aa798a956c2fe6a9eff88ac0888fc04000000001976"  # noqa
            "a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac00000000",  # noqa
            mtx.serialize().hex())

    # https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#native-p2wpkh
    def test_native_p2wpkh(self) -> None:
        input_list = [
            self._createInput(
                self._coin,
                name="fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f",  # noqa
                index=0,
                private_key="bbc27228ddcb9209d7fd6f36b02f7dfa6252af40bb2f1cbc7a557da8027ff866",  # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                script_type=self._coin.Script.Type.P2PK,
                amount=625000000,
                sequence=0xffffffee),
            self._createInput(
                self._coin,
                name="ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a",  # noqa
                index=1,
                private_key="619c335025c7f4012e556c2a58b2506e30b8511b53ade95ea316fd8c3286feb9",  # noqa
                address_type=self._coin.Address.Type.WITNESS_V0_KEY_HASH,
                script_type=self._coin.Script.Type.P2WPKH,
                amount=600000000,
                sequence=0xffffffff),
        ]
        output_list = [
            self._createOutput(
                self._coin,
                address_name="1Cu32FVupVCgHkMMRJdYJugxwo2Aprgk7H",  # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                amount=112340000
            ),
            self._createOutput(
                self._coin,
                address_name="16TZ8J6Q5iZKBWizWzFAYnrsaox5Z5aBRV",  # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                amount=223450000)
        ]

        mtx = self._coin.TxFactory.MutableTx(
            self._coin,
            input_list,
            output_list,
            lock_time=0x11)
        self.assertTrue(mtx.sign())
        self.assertEqual(
            "e8151a2af31c368a35053ddd4bdb285a8595c769a3ad83e0fa02314a602d4609",  # noqa
            mtx.name)

        self.assertEqual(
            "01000000000102fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf43354"  # noqa
            "1db4e4ad969f00000000494830450221008b9d1dc26ba6a9cb62127b02742fa9d7"  # noqa
            "54cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a99f2b1c0a19c"  # noqa
            "0489bc22ede944ccf4ecbab4cc618ef3ed01eeffffffef51e1b804cc89d182d279"  # noqa
            "655c3aa89e815b1b309fe287d9b2b55d57b90ec68a0100000000ffffffff02202c"  # noqa
            "b206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac90"  # noqa
            "93510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac"  # noqa
            "000247304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb13"  # noqa
            "66d7f01cc44a0220573a954c4518331561406f90300e8f3358f51928d43c212a8c"  # noqa
            "aed02de67eebee0121025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253"  # noqa
            "f62fc70f07aeee635711000000",  # noqa
            mtx.serialize().hex())

    # https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#p2sh-p2wpkh
    def test_p2sh_p2wpkh(self) -> None:
        input_list = [
            self._createInput(
                self._coin,
                name="db6b1b20aa0fd7b23880be2ecbd4a98130974cf4748fb66092ac4d3ceb1a5477",  # noqa
                index=1,
                private_key="eb696a065ef48a2192da5b28b694f87544b30fae8327c4510137a922f32c6dcf",  # noqa
                address_type=self._coin.Address.Type.WITNESS_V0_KEY_HASH,
                script_type=self._coin.Script.Type.P2SH_P2WPKH,
                amount=1000000000,
                sequence=0xfffffffe),
        ]
        output_list = [
            self._createOutput(
                self._coin,
                address_name="1Fyxts6r24DpEieygQiNnWxUdb18ANa5p7",  # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                amount=199996600),
            self._createOutput(
                self._coin,
                address_name="1Q5YjKVj5yQWHBBsyEBamkfph3cA6G9KK8",  # noqa
                address_type=self._coin.Address.Type.PUBKEY_HASH,
                amount=800000000)
        ]

        mtx = self._coin.TxFactory.MutableTx(
            self._coin,
            input_list,
            output_list,
            lock_time=0x492)
        self.assertTrue(mtx.sign())
        self.assertEqual(
            "ef48d9d0f595052e0f8cdcf825f7a5e50b6a388a81f206f3f4846e5ecd7a0c23",  # noqa
            mtx.name)

        self.assertEqual(
            "01000000000101db6b1b20aa0fd7b23880be2ecbd4a98130974cf4748fb66092ac"  # noqa
            "4d3ceb1a5477010000001716001479091972186c449eb1ded22b78e40d009bdf00"  # noqa
            "89feffffff02b8b4eb0b000000001976a914a457b684d7f0d539a46a45bbc043f3"  # noqa
            "5b59d0d96388ac0008af2f000000001976a914fd270b1ee6abcaea97fea7ad0402"  # noqa
            "e8bd8ad6d77c88ac02473044022047ac8e878352d3ebbde1c94ce3a10d057c2417"  # noqa
            "5747116f8288e5d794d12d482f0220217f36a485cae903c713331d877c1f64677e"  # noqa
            "3622ad4010726870540656fe9dcb012103ad1d8e89212f0b92c74d23bb710c0066"  # noqa
            "2ad1470198ac48c43f7d6f93a2a2687392040000",
            mtx.serialize().hex())
