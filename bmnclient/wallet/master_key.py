import os
import re
from typing import Optional

from PySide2.QtCore import Slot as QSlot, Signal as QSignal, \
    Property as QProperty, QObject

from bmnclient.config import UserConfig
from bmnclient.crypto.kdf import KeyDerivationFunction
from bmnclient.ui import CoreApplication
from bmnclient.ui.gui import import_export
from bmnclient.logger import getClassLogger
from . import hd, mnemonic, util

MNEMONIC_SEED_LENGTH = 24
PASSWORD_HASHER = util.sha256


class KeyManager(QObject):
    """
    Holding hierarchy  according to bip0044
    """
    activeChanged = QSignal()
    mnemoRequested = QSignal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent=parent)
        self._logger = getClassLogger(__name__, self.__class__)

        self._password_kdf = None
        self.__master_hd = None
        self.__mnemonic = mnemonic.Mnemonic()
        # don't keep mnemo, save seed instead !!!
        self.__seed = None
        # mb we can use one seed variable?
        self.__pre_hash = None

    @QSlot(str, result=bool)
    def preparePhrase(self, mnemonic_phrase: str) -> bool:
        mnemonic_phrase = " ".join(mnemonic_phrase.split())
        self._logger.debug(f"pre phrase: {mnemonic_phrase}")
        self.__pre_hash = util.sha256(mnemonic_phrase)
        return True

    @QSlot(str, bool, result=bool)
    def generateMasterKey(self, mnemonic_phrase: str, debug: bool = False) -> bool:
        mnemonic_phrase = " ".join(mnemonic_phrase.split())
        hash_ = util.sha256(mnemonic_phrase)
        if self.__pre_hash is None or hash_ == self.__pre_hash:
            seed = mnemonic.Mnemonic.to_seed(
                mnemonic_phrase,
            )
            self.apply_master_seed(
                seed,
                save=True,
            )
            self.gcd.save_mnemo(mnemonic_phrase)
            return True
        self._logger.warning(
            f"seed '{mnemonic_phrase}' mismatch: {hash_} != {self.__pre_hash}")
        return False

    @QSlot(float, result=str)
    def getInitialPassphrase(self, extra__seed: float = None) -> str:
        data = os.urandom(MNEMONIC_SEED_LENGTH)
        if extra__seed:
            # a little bit silly but let it be
            data = util.sha256(data + str(extra__seed).encode()
                               )[:MNEMONIC_SEED_LENGTH]
        else:
            self._logger.warning("No extra!!!")
        return self.__mnemonic.get_phrase(data)

    def regenerate_master_key(self):
        seed = mnemonic.Mnemonic.to_seed(
            self.gcd.get_mnemo(),
        )
        self.apply_master_seed(
            seed,
            save=True,
        )

    @QSlot(str, result=str)
    def revealSeedPhrase(self, password: str):
        return self.gcd.get_mnemo(password) or self.tr("Wrong password")

    @QProperty(bool, notify=activeChanged)
    def hasMaster(self):
        self._logger.debug(f"master key:{self.__master_hd}")
        return self.__master_hd is not None

    @QSlot()
    def resetWallet(self):
        self.gcd.reset_wallet()
        self.mnemoRequested.emit()

    @QSlot()
    def exportWallet(self):
        iexport = import_export.ImportExportDialog()
        filename = iexport.doExport(
            self.tr("Select file to save backup copy"))
        if filename:
            self.gcd.export_wallet(filename)

    @QSlot(result=bool)
    def importWallet(self) -> bool:
        iexport = import_export.ImportExportDialog()
        filename = iexport.doImport(
            self.tr("Select file with backup"))
        self._logger.debug(f"Import result: {filename}")
        if filename:
            self.gcd.import_wallet(filename)
            return True
        return False

    def apply_master_seed(self, seed: bytes, *, save: bool):
        """
        applies master seed
        """
        self.__seed = seed
        self.__master_hd = hd.HDNode.make_master(self.__seed)
        _44_node = self.__master_hd.make_child_prv(44, True)
        # iterate all 'cause we need test coins
        for coin in self.gcd.all_coins:
            if coin.enabled:
                coin.make_hd_node(_44_node)
                self._logger.debug(f"Make HD prv for {coin}")
        if save:
            self.gcd.save_master_seed(self.master_seed_hex)
        self.activeChanged.emit()

    @QSlot(str, result=bool)
    def validateSeed(self, seed: str) -> bool:
        try:
            self.__mnemonic.check_words(seed)
            return True
        except ValueError as ve:
            self._logger.warning(f"seed validation error: {ve} => {seed}")
            return False

    @property
    def gcd(self):
        return self.parent()

    @property
    def master_key(self):
        return self.__master_hd

    @property
    def master_seed_hex(self) -> str:
        return util.bytes_to_hex(self.__seed)

    @QSlot(str, result=int)
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

    @QSlot(str, result=bool)
    def createPassword(self, password: str) -> bool:
        user_config = CoreApplication.instance().userConfig
        kdf = KeyDerivationFunction()
        kdf.setPassword(password)
        return user_config.set(
            UserConfig.KEY_WALLET_SECRET,
            kdf.createSecret())

    @QSlot(str, result=bool)
    def applyPassword(self, password: str) -> bool:
        user_config = CoreApplication.instance().userConfig
        secret = user_config.get(UserConfig.KEY_WALLET_SECRET, str)
        if not secret:
            return False

        kdf = KeyDerivationFunction()
        kdf.setPassword(password)
        if not kdf.verifySecret(secret):
            return False
        self._password_kdf = kdf

        self.gcd.apply_password(self._password_kdf)  # TODO
        return True

    @QSlot()
    def resetPassword(self) -> bool:
        user_config = CoreApplication.instance().userConfig
        if user_config.set(UserConfig.KEY_WALLET_SECRET, None):
            self.gcd.reset_db()  # TODO
            return True
        return False

    @QProperty(bool, constant=True)
    def hasPassword(self) -> bool:
        user_config = CoreApplication.instance().userConfig
        secret = user_config.get(UserConfig.KEY_WALLET_SECRET, str)
        return secret and len(secret) > 0
