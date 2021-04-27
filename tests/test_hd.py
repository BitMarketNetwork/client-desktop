import logging
import os
import random
import unittest

from bmnclient.coins import mnemonic
from bmnclient.coins.hd import HdAddressIterator
from bmnclient.wallet import coin_network, hd, key as key_mod
from bmnclient.wallet.coins import Bitcoin
from bmnclient.wallet.hd import HDNode


class TestHdAddressIterator(unittest.TestCase):
    def setUp(self) -> None:
        root_path = HDNode.make_master(random.randbytes(64))
        self._purpose_path = root_path.make_child_prv(44, True)

    def test(self) -> None:
        coin = Bitcoin()
        coin.makeHdPath(self._purpose_path)

        flush = 0
        append = 0
        it = None
        while flush < 1 or append < 0:
            it = HdAddressIterator(coin)
            flush = 0
            append = 0

            for address in it:
                if random.randint(0, 2) == 1:
                    flush += 1
                    it.appendAddressToEmptyList(address)
                    # noinspection PyProtectedMember
                    self.assertGreater(len(it._empty_address_list), 0)
                else:
                    append += 1
                    it.appendAddressToCoin(address)
                    # noinspection PyProtectedMember
                    self.assertEqual(
                        len(it._empty_address_list[address.addressType]),
                        0)
            self.assertRaises(StopIteration, next, it)

        self.assertIsNotNone(it)
        # noinspection PyProtectedMember
        self.assertEqual(len(it._empty_address_list), 2)
        self.assertGreater(len(coin.addressList), 0)

        # noinspection PyProtectedMember
        for (address_type, address_list) in it._empty_address_list.items():
            # noinspection PyProtectedMember
            self.assertEqual(len(address_list), it._EMPTY_ADDRESS_LIMIT)


log = logging.getLogger(__name__)
MNEMO_PASSWORD = "hardcoded mnemo password"

@unittest.skip
class TestBase(unittest.TestCase):

    def test_btc(self):
        seed = mnemonic.Mnemonic.phraseToSeed(
            "minimum crowd cruel boil truck mirror drop source urge ritual various napkin",
            MNEMO_PASSWORD,
        )
        net = coin_network.BitcoinMainNetwork
        master = hd.HDNode.make_master(seed)
        h44 = master.make_child_prv(44, True)
        btc_hd = h44.make_child_prv(0, True, net)
        for i in range(0, 20):
            hdk = btc_hd.make_child_prv(i, False, net)
            addr = hdk.to_address(key_mod.AddressType.P2WPKH)
            log.warning(f"{i}: {addr} hdpath:{hdk.chain_path}")


class TestAdvanced(unittest.TestCase):

    def test_free_coin_index(self):
        coin = coins.Bitcoin(None)
        dummy = hd.HDNode.make_master(os.urandom(64))
        coin.makeHdPath(dummy)
        self.assertEqual(coin._next_hd_index(), 1)
        coin.make_address()
        self.assertEqual(coin._next_hd_index(), 2)
        w2 = coin.make_address()
        coin.make_address()
        self.assertEqual(coin._next_hd_index(), 4)
        coin.remove_wallet(w2)
        # the key is here !!!!
        self.assertEqual(coin._next_hd_index(), 2)

    def test_main(self):

        ITERS = 1000
        VARIATIONS = 3  # uni factor
        HD_DEPTH = 20
        mnemo = mnemonic.Mnemonic()
        # important!!
        random.seed()
        rfactors = [random.randint(1e2, 1e6)
                    for _ in range(ITERS)] * VARIATIONS
        random.shuffle(rfactors)

        def cmp(d1: dict, d2: dict, deep: bool = False) -> None:
            if deep:
                for (k, v1), (_, v2) in zip(d1.items(), d2.items()):
                    self.assertEqual(v1, v2, k)
            else:
                self.assertEqual(d1, d2)

        def do_for_coin(coin_class):
            cache = {}
            for i, f in enumerate(rfactors):
                if 0 == i % 100:
                    log.warning(f"iteration:{i}: seed:{f}")
                # crucial !!
                coin = coin_class(None)
                random.seed(a=f)
                # words_combs = itertools.combinations(
                #     random.shuffle(mnemo._wordlist, f), master_key.MNEMONIC_SEED_LENGTH)
                words = random.choices(
                    mnemo._wordlist, k=key_store.MNEMONIC_SEED_LENGTH)
                phraze = " ".join(words)
                cache_entry = {}
                cache_entry["phraze"] = phraze
                master_seed = mnemo.phraseToSeed(phraze)
                cache_entry["master"] = master_seed
                master = hd.HDNode.make_master(master_seed)
                self.assertIsNotNone(master)
                h44 = master.make_child_prv(44, True)
                cache_entry["44"] = h44.to_hex
                coin.makeHdPath(h44)
                # hm
                wif = coin.hd_node.to_wif
                check = key_mod.PrivateKey.from_wif(wif)
                self.assertEqual(coin.hd_node.to_hex, check.to_hex)
                cache_entry["coin"] = coin.hd_node.to_hex
                for i in range(0, HD_DEPTH):
                    addr = coin.make_address()
                    cache_entry[f"_{i}_name"] = addr.name
                    cache_entry[f"_{i}_key"] = addr.to_wif

                # log.warning(
                    # f"\n\nnew iteration. factor:{f} entry:{cache_entry}")
                ###
                old_entry = cache.setdefault(f, cache_entry)
                wrong_entries = (v for k, v in cache.items() if k != f)
                self.assertEqual(old_entry['phraze'], phraze)
                cmp(cache_entry, old_entry)
                for i, w in enumerate(wrong_entries):
                    self.assertNotEqual(w, cache_entry)
                    if i > VARIATIONS:
                        break

        ##
        do_for_coin(coins.Bitcoin)
        do_for_coin(coins.Litecoin)
