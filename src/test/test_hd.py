
import unittest
import logging
from client.wallet import key as key_mod, hd, mnemonic, coin_network
log = logging.getLogger(__name__)
MNEMO_PASSWORD = "hardcoded mnemo password"


class Test_Base(unittest.TestCase):

    def test_btc(self):
        seed = mnemonic.Mnemonic.to_seed(
            "minimum crowd cruel boil truck mirror drop source urge ritual various napkin",
            MNEMO_PASSWORD,
        )
        net = coin_network.BitcoinMainNetwork
        master = hd.HDNode.make_master(seed, net)
        h44 = master.make_child_prv(44, True)
        btc_hd = h44.make_child_prv(0, True, net)
        for i in range(0, 20):
            hdk = btc_hd.make_child_prv(i, False, net)
            addr = hdk.to_address(key_mod.AddressType.P2WPKH)
            log.warning(f"{i}: {addr} hdpath:{hdk.chain_path}")
