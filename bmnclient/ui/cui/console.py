import logging
import getpass
from ...application import CoreApplication

import PySide2.QtCore as qt_core

# for static calls
import bmnclient.version as e_config_version
from bmnclient.wallet import coins
from . import app
from . import cmd_base

log = logging.getLogger(__name__)


class Console(cmd_base.Cmd, qt_core.QObject, CoreApplication):

    WALLET_SUB_COMMANDS = [
        "add",
        "info",
        "list",
        "poll",
        "update",
    ]

    def __init__(self, gcd):
        super().__init__()
        # TODO: dirty
        qt_core.QObject.__init__(self, parent=gcd)
        self.gcd = gcd
        self.intro = self.tr(f'Welcome to {e_config_version.NAME}.\tType help or ? to list commands.\n')
        self.doc_header = self.tr("Documentation:")
        self.misc_header = self.tr("Misc")
        self.undoc_header = self.tr("Details")
        self.use_rawinput = False
        self._app = app.ConsoleApp()
        self._input = cmd_base.InputThread(self)

    def on_line(self, line):
        line = self.precmd(line)
        stop = self.onecmd(line)
        stop = self.postcmd(stop, line)
        if stop:
            log.warning("Exit app")
            self.gcd.quit(0)

    def exec_(self):
        self._input.start()
        return self._app.exec_()

    def precmd(self, line):
        return line

    def postcmd(self, stop, line):
        return stop

    def default(self, line):
        self._print(self.tr(f'Command `{line}` isn`t recognized. Type `help` for full list.'))
        # self.gcd.quit(1)

    def preloop(self):
        pass

    def postloop(self):
        log.debug('cui goin` to exit')
        #
        log.fatal("Temporary emergency exit")

    def _get_password(self, confirm=False):
        passw = getpass.getpass(self.tr('Setup your password:'))
        if passw:
            if confirm:
                if passw == getpass.getpass(self.tr('Type this password again to confirm:')):
                    return passw
            else:
                return passw
            self._print('Try to create password again')

    def do_serverinfo(self, arg):
        """
        Retrieve server system information
        """
        self.gcd.serverInfo()

    def do_coinsinfo(self, arg):
        """
        Retrieve server coins information
        """
        # self.gcd.coins_info()

    def help_wallet(self):
        print("Available commands: %s" % ", ".join(self.WALLET_SUB_COMMANDS))

    def complete_wallet(self, text, line, begidx, endidx):
        if text:
            return [cd for cd in self.WALLET_SUB_COMMANDS if cd.startswith(text)]
        return self.WALLET_SUB_COMMANDS[:]

    def do_wallet(self, arg):
        "Working with wallet"
        cmds = arg.split()
        if not cmds:
            return self.help_wallet()
        if cmds[0] not in self.WALLET_SUB_COMMANDS:
            raise cmd_base.ConsoleInputError(
                self.tr("Unknown wallet command:%s") % cmds[0])
        if "list" == cmds[0]:
            def show_coin(coin):
                self._print(f"{coin.full_name} wallets:")
                for w in coin:
                    self._print(w)
            show_coin(self.gcd.btc_coin)
            show_coin(self.gcd.ltc_coin)
        elif "poll" == cmds[0]:
            self.gcd.debug_man.poll()
        elif "add" == cmds[0] and len(cmds) > 2:
            self.gcd.add_address(cmds[2], cmds[1])
        elif len(cmds) < 2:
            raise cmd_base.ConsoleInputError(
                self.tr("Select wallet to work with"))
        else:
            try:
                if "info" == cmds[0]:
                    self.gcd.get_address_info(cmds[1])
                elif "history" == cmds[0]:
                    self.gcd.get_address_history(cmds[1])
                elif "update" == cmds[0]:
                    self.gcd.silent_mode = False
                    self.gcd.update_wallet(cmds[1])
                else:
                    raise cmd_base.ConsoleInputError(
                        self.tr("Wrong wallet command's usage"))
            except coins.SelectAddressError as wer:
                raise cmd_base.ConsoleInputError(wer)
