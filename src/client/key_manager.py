
import logging
import os
import re
import PySide2.QtCore as qt_core
from .wallet import hd
from .wallet import coin_network
from .wallet import mnemonic
from .wallet import util
from client.ui.gui import import_export

log = logging.getLogger(__name__)

MNEMONIC_SEED_LENGTH = 16
PASSWORD_HASHER = util.sha256
MNEMO_PASSWORD = "hardcoded mnemo password"


class KeyManager(qt_core.QObject):
    """
    Holding hierarchy  according to bip0044
    """
    activeChanged = qt_core.Signal()
    mnemoRequested = qt_core.Signal()

    def __init__(self, parent):
        super().__init__(parent=parent)
        self._master_hd = None
        self._network = coin_network.BitcoinMainNetwork()
        self._mnemonic = mnemonic.Mnemonic()
        # don't keep mnemo, save seed instead !!!
        self._seed = None
        # mb we can use one seed variable?
        self._pre_hash = None
        self._backup_password = ""

    @qt_core.Slot(str, result=bool)
    def preparePhrase(self, mnemonic_phrase: str) -> bool:
        log.debug(f"pre phrase: {mnemonic_phrase}")
        self._pre_hash = util.sha256(mnemonic_phrase)
        # mnemonic.Mnemonic.to_seed( mnemonic_phrase, MNEMO_PASSWORD,)
        return True

    @qt_core.Slot(str, bool, result=bool)
    def generateMasterKey(self, mnemonic_phrase: str, debug: bool = False) -> bool:
        mnemonic_phrase = " ".join(mnemonic_phrase.split(" "))
        if debug:
            return True
        hash_ = util.sha256(mnemonic_phrase)
        if self._pre_hash is None or hash_ == self._pre_hash:
            seed = mnemonic.Mnemonic.to_seed(
                mnemonic_phrase,
                MNEMO_PASSWORD,
                )
            self.apply_master_seed(
                seed,
                save=True,
            )
            return True
        log.warning(f"seed '{mnemonic_phrase}' mismatch: {hash_} != {self._pre_hash}")
        return False

    @qt_core.Slot(int, result=str)
    def getInitialPassphrase(self, extra_seed: int = None) -> str:
        data = os.urandom(MNEMONIC_SEED_LENGTH)
        if extra_seed:
            extra_bytes = util.number_to_bytes(
                abs(extra_seed), MNEMONIC_SEED_LENGTH)
            # TODO: week point here ... not xor it ... there is a lot another options
            data = util.xor_bytes(data, extra_bytes)
        return self._mnemonic.get_phrase(data)

    @qt_core.Property(bool, notify=activeChanged)
    def hasMaster(self):
        log.debug(f"master key:{self._master_hd}")
        return self._master_hd is not None

    @qt_core.Slot()
    def resetWallet(self):
        self.gcd.reset_wallet()
        self.mnemoRequested.emit()

    @qt_core.Slot()
    def exportWallet(self):
        iexport = import_export.ImportExportDialog()
        filename = iexport.doExport(
            self.tr("Select file to save backup copy"))
        if filename:
            self.gcd.export_wallet(filename)

    @qt_core.Slot(result=bool)
    def importWallet(self) -> bool:
        iexport = import_export.ImportExportDialog()
        filename = iexport.doImport(
            self.tr("Select file with backup"))
        log.debug(f"Import result: {filename}")
        if filename:
            self.gcd.import_wallet(filename)
            return True
        return False

    def apply_master_seed(self, seed: bytes, *, save: bool):
        """
        applies master seed
        """
        self._seed = seed
        log.debug(f"master seed applied: {seed}")
        self._master_hd = hd.HDNode.make_master(
            self._seed, self._network)
        _44_node = self._master_hd.make_child_prv(44, True)
        # iterate all 'cause we need test coins
        for coin in self.gcd.all_coins:
            if coin.enabled:
                coin.make_hd_node(_44_node)
                log.debug(f"Make HD prv for {coin}")
        if save:
            self.gcd.save_master_seed(self.master_seed_hex)
        self.activeChanged.emit()

    @property
    def gcd(self):
        return self.parent()

    @property
    def master_key(self):
        return self._master_hd

    @property
    def master_seed_hex(self) -> str:
        return util.bytes_to_hex(self._seed)

    @qt_core.Slot(str)
    def setNewPassword(self, password: str) -> None:
        self.gcd.set_password(password)

    @qt_core.Slot(str, result=int)
    def validatePasswordStrength(self, password: str) -> int:
        unique = "".join(set(password))
        if not password or len(password) < 8:
            return 1
        if len(unique) < 6:
            return 2
        password_strength = dict.fromkeys(
            ['has_upper', 'has_lower', 'has_num', 'has_sep'], False)
        if re.search(r'[A-Z]', password):
            password_strength['has_upper'] = True
        if re.search(r'[a-z]', password):
            password_strength['has_lower'] = True
        if re.search(r'[0-9]', password):
            password_strength['has_num'] = True
        if re.search(r'[;+-@=#$%^&":{}\(\)]', password):
            password_strength['has_sep'] = True
        res = len([b for b in password_strength.values() if b])
        if len(password) > 16:
            res += 1
        if len(unique) > 10:
            res += 1
        return res

    @qt_core.Slot(str, result=bool)
    def testPassword(self, password: str) -> bool:
        return self.gcd.test_password(password)

    @qt_core.Slot(str, result=bool)
    def applyPassword(self, password: str) -> None:
        return self.gcd.apply_password(None)

    @qt_core.Slot()
    def removePassword(self) -> None:
        return self.gcd.remove_password()

    @qt_core.Property(bool, constant=True)
    def hasPassword(self) -> bool:
        return self.gcd.has_password()