import logging
from typing import Optional, List
import sqlite3 as sql
import sys
import traceback
from pathlib import Path
from contextlib import closing
# to debug
from ...server import net_cmd
import bmnclient.config

import PySide2.QtCore as qt_core

from .. import address, coins, tx
from . import sqlite_impl

log = logging.getLogger(__name__)


def nmark(number: int) -> str:
    return f"({','.join('?'*number)})"


class DatabaseError(Exception):
    pass


class DbWrapper:
    """
    Command wrappers here
    """
    DEFAULT_DB_NAME = str(bmnclient.config.USER_DATABASE_FILE_PATH)

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self._save_address_timer: qt_core.QBasicTimer = qt_core.QBasicTimer()
        self._save_address_timer.wallet = None
        self.__db_name = None
        self.__impl = sqlite_impl.SqLite()

    def open_db(self) -> None:
        self.__db_name = self.DEFAULT_DB_NAME
        self.__impl.connect_impl(self.__db_name)
        self.__impl.create_tables()

    def close_db(self) -> None:
        self.__impl.close()

    def drop_db(self) -> None:
        self.close_db()
        if self.__db_name:
            pth = Path(self.__db_name)
            self.__db_name = None
            if pth.exists():
                pth.unlink()

    def reset_db(self, password: str) -> None:
        self.drop_db()
        self.open_db()

    @classmethod
    def has_db(cls) -> bool:
        return Path(cls.__db_name).exists()

    def __exec(self, query: str, args: tuple = ()):
        return self.__impl.exec(query, args)

    def _add_coin(self, coin: coins.CoinType, read_addresses=False) -> None:
        """
        - insert coin if not exists
        - set rowid for coin
        - read wallets
        """
        name = self.__impl(coin.name)
        height = self.__impl(coin.height)
        verified_height = self.__impl(coin.verified_height)
        offset = self.__impl(coin.offset)
        unverified_offset = self.__impl(coin.unverified_offset)
        unverified_signature = self.__impl(coin.unverified_signature)
        rate = self.__impl(coin.rate)
        visible = self.__impl(coin.visible)
        try:
            query = f"""
            INSERT OR IGNORE INTO {self.coins_table}
                (
                {self.name_column},
                {self.visible_column},
                {self.height_column},
                {self.verified_height_column},
                {self.offset_column},
                {self.unverified_offset_column},
                {self.unverified_signature_column},
                {self.rate_usd_column}
                )
                VALUES  {nmark(8)}
            """
            cur = self.__impl.exec(query, (
                name,
                visible,
                height,
                verified_height,
                offset,
                unverified_offset,
                unverified_signature,
                rate,
            ))
        except sql.IntegrityError as ie:
            log.error("DB integrity: %s (%s)", ie, coin)
        ##
        if coin.rowid is None and cur.lastrowid:
            coin.rowid = cur.lastrowid
            cur.close()
            query = f"""
                SELECT {self.visible_column} FROM {self.coins_table} WHERE id == ?;
            """
            with closing(self.__exec(query, (coin.rowid,))) as c:
                res = c.fetchone()
                coin.visible = res[0]
        else:
            query = f"""
                SELECT id , {self.visible_column} FROM {self.coins_table} WHERE {self.name_column} == ?;
            """
            with closing(self.__exec(query, (name,))) as c:
                res = c.fetchone()
                coin.rowid = res[0]
                coin.visible = res[1]
                log.debug(f"coin exists:{coin} : {res}")
        log.debug(f"Add COIN to db {coin} = {name} read addr:{read_addresses}")
        #
        if read_addresses:
            self._read_address_list(coin)
        coin.update_balance()

    def _update_coin(self, coin: coins.CoinType) -> None:
        """
        _add_coin can do it but it isn't straight
        """
        if not coin.rowid:
            log.warning("NO COIN ROW")
            return
        try:
            query = f"""
            UPDATE {self.coins_table} SET
                {self.visible_column} = ?,
                {self.height_column} = ?,
                {self.verified_height_column} = ?,
                {self.offset_column} = ?,
                {self.unverified_offset_column} = ?,
                {self.unverified_signature_column} = ?,
                {self.rate_usd_column} = ?
                WHERE id = ?;
            """

            with closing(self.__exec(query, (
                self.__impl(coin.visible),
                self.__impl(coin.height),
                self.__impl(coin.verified_height),
                self.__impl(coin.offset),
                self.__impl(coin.unverified_offset),
                self.__impl(coin.unverified_signature),
                self.__impl(coin.rate),
                coin.rowid,
            ))) as c:
                pass
        except sql.IntegrityError as ie:
            log.error("DB integrity: %s (%s)", ie, coin)

    def _read_address_list(self, coin: coins.CoinType):
        # strict order of columns!! stick to the make_address !!
        query = f"""
        SELECT
            {self.address_column},
            id,
            {self.label_column},
            {self.message_column},
            {self.created_column},
            {self.type_column},
            {self.balance_column},
            {self.tx_count_column},
            {self.first_offset_column},
            {self.last_offset_column},
            {self.key_column}
        FROM {self.wallets_table} WHERE {self.coin_id_column} == ?;
        """
        with closing(self.__exec(query, (coin.rowid,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            wallet = coin.append_address(*values)
            self._read_tx_list(wallet)
            wallet.valid = True
            ##
            # self.update_wallet.emit(wallet)

    def _read_tx_list(self, wallet: address.CAddress) -> None:
        query = f"""
            SELECT
                id,
                {self.name_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
                {self.status_column}
            FROM {self.transactions_table} WHERE {self.wallet_id_column} == ?;
        """
        with closing(self.__exec(query, (wallet.rowid,))) as c:
            fetch = c.fetchall()
        txs = []
        for values in fetch:
            qt_core.QCoreApplication.processEvents()
            tx_ = tx.Transaction(None)
            tx_.from_args(iter(values))
            txs.append(tx_)
            self._read_input_list(tx_)
        wallet.add_tx_list(txs)

    def _read_input_list(self, tx: tx.Transaction) -> None:
        """
        and outputs too of course
        """
        assert tx.rowid
        query = f"""
            SELECT
                {self.type_column},
                {self.address_column},
                {self.amount_column},
                {self.output_type_column}
            FROM {self.inputs_table} WHERE {self.tx_id_column} == ?;
        """
        with closing(self.__exec(query, (tx.rowid,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            tx.make_input(iter(values))
        qt_core.QCoreApplication.processEvents()

    def _read_tx_count(self, wallet: address.CAddress) -> None:
        query = f"""
        SELECT Count(*) FROM {self.transactions_table}
        WHERE {self.wallet_id_column} == ?;
        """
        with closing(self._exec_(query, (wallet.rowid,))) as c:
            fetch = c.fetchone()
        return fetch[0]

    def _clear_tx(self, address: address.CAddress) -> None:
        query = f"""
        DELETE FROM {self.transactions_table}
        WHERE {self.wallet_id_column} == ?;
        """
        with closing(self.__exec(query, (address.rowid,))):
            pass

    def _remove_tx(self, tx_: tx.Transaction) -> None:
        if tx_.rowid is None:
            query = f"""
            DELETE FROM {self.transactions_table}
            WHERE {self.name_column} == ?;
            """
            with closing(self.__exec(query, (self.__impl(tx_.name),))):
                pass
        else:
            query = f"""
            DELETE FROM {self.transactions_table}
            WHERE id == ?;
            """
            with closing(self.__exec(query, (self.__impl(tx_.rowid),))):
                pass

    def _remove_tx_list(self, tx_list: List[tx.Transaction]) -> None:
        # TODO: optimize
        # may be row ids?
        # tx_hashes = f"({','.join(map(lambda t: self.__impl(t.name),tx_list))})"
        # log.warning(f"tx hashes:{tx_hashes}")
        # query = f"""
        # DELETE FROM {self.transactions_table}
        # WHERE {self.name_column} IN ?;
        # """
        # self._exec_(query, (tx_list,))

        for tx_ in tx_list:
            self._remove_tx(tx_)

    def _add_or_save_wallet(self, wallet: address.CAddress, timeout: int = None) -> None:
        if wallet.is_root:
            log.error(f"attempt to save root address")
            traceback.print_stack()
            return
        if not timeout:
            self._add_or_save_wallet_impl(wallet)
        else:
            if self._save_address_timer.wallet and self._save_address_timer.wallet is not wallet:
                self._add_or_save_wallet_impl(self._save_address_timer.wallet)
            self._save_address_timer.wallet = wallet
            self._save_address_timer.start(timeout, self)

    def _add_or_save_wallet_impl(self, wallet: address.CAddress) -> None:
        if wallet.is_root:
            return
        assert wallet.coin.rowid
        if wallet.rowid is None:
            query = f"""
            INSERT  INTO {self.wallets_table}
                (
                    {self.address_column},
                    {self.coin_id_column},
                    {self.label_column},
                    {self.message_column},
                    {self.created_column},
                    {self.type_column},
                    {self.balance_column},
                    {self.tx_count_column},
                    {self.first_offset_column},
                    {self.last_offset_column},
                    {self.key_column}
                )
                VALUES  {nmark(11)}
                ;
            """
            try:
                with closing(self.__exec(query, (
                    self.__impl(wallet.name),
                    wallet.coin.rowid,  # don't encrypt!
                    self.__impl(wallet.label, True, "wallet label"),
                    self.__impl(wallet.message, True, "wallet message"),
                    self.__impl(wallet.created_db_repr),
                    # they're  empty at first place but later not !
                    self.__impl(wallet.type),
                    self.__impl(wallet.balance),
                    self.__impl(wallet.txCount),
                    self.__impl(wallet.first_offset),
                    self.__impl(wallet.last_offset),
                    self.__impl(wallet.export_key(), True, "wallet key"),
                ))) as c:
                    wallet.rowid = c.lastrowid
                    wallet.valid = True

            except sql.IntegrityError as ie:
                log.warning(f"Can't add wallet:'{wallet}' => '{ie}'")
                # it can happen if user adds existing address
                # sys.exit(1)
            """
            we don't put some fields in update scope cause we don't expect them being changed
            """
        else:
            if net_cmd.AddressHistoryCommand.verbose:
                log.debug("saving wallet info %r" % wallet)
            query = f"""
            UPDATE  {self.wallets_table} SET
                {self.label_column} = ?,
                {self.type_column} = ?,
                {self.balance_column} = ?,
                {self.tx_count_column} = ?,
                {self.first_offset_column} = ?,
                {self.last_offset_column} = ?
            WHERE id = ?
                ;
            """

            try:
                with closing(self.__exec(query, (
                    self.__impl(wallet.label, True, "wallet label"),
                    self.__impl(wallet.type),
                    self.__impl(wallet.balance),
                    self.__impl(wallet.txCount),
                    self.__impl(wallet.first_offset),
                    self.__impl(wallet.last_offset),
                    wallet.rowid
                ))):
                    pass
            except sql.IntegrityError as ie:
                log.error(f"DB integrity: {ie} for {wallet}")
            except sql.InterfaceError as ie:
                log.error(f"DB integrity: {ie}  for {wallet}")

    def _erase_wallet(self, wallet: address.CAddress) -> None:
        assert wallet.rowid
        query = f"""
            DELETE FROM {self.wallets_table}
            WHERE id == ?
        """
        with closing(self.__exec(query, (wallet.rowid,))):
            pass
        self._clear_tx(wallet)
        log.debug(f"Wallet {wallet} erased from DB")

    def _apply_password(self) -> None:
        self.open_db()
        self._init_actions()

    def _write_transaction(self, tx: tx.Transaction) -> None:
        try:
            query = f"""
            INSERT  INTO {self.transactions_table}
                ({self.name_column},
                {self.wallet_id_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
                {self.coin_base_column}
                ) VALUES  {nmark(7)}
            """
            assert tx.wallet.rowid is not None
            with closing(self.__exec(query,
                                     (
                                         self.__impl(tx.name),
                                         tx.wallet.rowid,
                                         self.__impl(tx.height),
                                         self.__impl(tx.time),
                                         self.__impl(tx.balance),
                                         self.__impl(tx.fee),
                                         self.__impl(tx.coin_base),
                                     ))) as c:
                tx.rowid = c.lastrowid
            # make it in try block ( we don't need inputs withot tx )
            # inputs
            for inp in tx.inputs:
                self._write_input(inp)
            for out in tx.outputs:
                self._write_input(out)

        except sql.IntegrityError as ie:
            # TODO: adjust query instead
            if str(ie).find('UNIQUE') < 0:
                log.fatal("TX exists: %s (%s)", tx, ie)
                sys.exit(1)
            else:
                # log.warn(f"Can't save TX:{ie}")
                pass
        except AssertionError:
            sys.exit(1)

    def _write_transactions(self, address, tx_list: list) -> None:
        # log.warning(f"{address} {tx_list}")
        assert address.rowid is not None
        self._gcd.post_count -= 1
        for tx in tx_list:
            try:
                query = f"""
                INSERT  INTO {self.transactions_table}
                    ({self.name_column},
                    {self.wallet_id_column},
                    {self.height_column},
                    {self.time_column},
                    {self.amount_column},
                    {self.fee_column},
                    {self.coin_base_column}
                    ) VALUES  {nmark(7)}
                """
                with closing(self.__exec(query,
                                         (
                                             self.__impl(tx.name),
                                             address.rowid,
                                             self.__impl(tx.height),
                                             self.__impl(tx.time),
                                             self.__impl(tx.balance),
                                             self.__impl(tx.fee),
                                             self.__impl(tx.coin_base),
                                         ))) as c:
                    tx.rowid = c.lastrowid
                # make it in try block ( we don't need inputs withot tx )
                # inputs
                for inp in tx.inputs:
                    self._write_input(inp)
                for out in tx.outputs:
                    self._write_input(out)

            except sql.IntegrityError as ie:
                if str(ie).find('UNIQUE') < 0:
                    log.fatal("TX exists: %s (%s)", tx, ie)
                    sys.exit(1)
                else:
                    log.debug(f"Can't save TX:{ie}")
                    pass
            except AssertionError:
                sys.exit(1)

    def _write_input(self, inp: tx.Input) -> None:
        """
        and outputs too of course
        """
        try:
            query = f"""
            INSERT INTO {self.inputs_table}
                ({self.address_column},{self.tx_id_column},{self.amount_column},{self.type_column},{self.output_type_column})
                VALUES  {nmark(5)}
            """
            with closing(self.__exec(query,
                                     (
                                         self.__impl(inp.address),
                                         inp.tx.rowid,
                                         self.__impl(inp.amount),
                                         self.__impl(inp.out),
                                         self.__impl(inp.type),
                                     ))):
                pass
        except sql.IntegrityError as ie:
            log.error("Input exists: %s (%s)", inp, ie)

    def _read_all_coins(self, coins_: List[coins.CoinType]) -> None:
        # read everything
        query = f"""
            SELECT
                id,
                {self.name_column},
                {self.visible_column},
                {self.height_column},
                {self.verified_height_column},
                {self.offset_column},
                {self.unverified_offset_column},
                {self.unverified_signature_column},
                {self.rate_usd_column}
                FROM {self.coins_table};
        """
        with closing(self.__exec(query)) as c:
            fetch = c.fetchall()
        if not fetch:
            for coin in coins_:
                self._add_coin(coin)
            return
        for (
            rowid,
            name,
            visible,
            height,
            vheight,
            offset,
            uoffset,
            usig,
            rate,
        ) in fetch:
            coin: coins.CoinType = next(
                (coin for coin in coins_ if coin.name == name), None)
            if coin is not None:
                coin.rowid = rowid
                coin.visible = visible
                coin.offset = offset
                coin.verified_height = vheight
                coin.unverified_offset = uoffset
                coin.unverified_signature = usig
                coin.rate = rate
                # let height will be the last
                coin.height = height
            else:
                log.warn(f"saved coin {name} isn't found ")

    def _read_all_addresses(self, coins: coins.CoinType) -> address.CAddress:
        assert coins
        """
        we call this version on start
        """
        query = f"""
        SELECT
            {self.coin_id_column},
            {self.address_column},
            id,
            {self.label_column},
            {self.message_column},
            {self.created_column},
            {self.type_column},
            {self.balance_column},
            {self.tx_count_column},
            {self.first_offset_column},
            {self.last_offset_column},
            {self.key_column}
        FROM {self.wallets_table}
        """
        with closing(self.__exec(query,)) as c:
            fetch = c.fetchall()
        # prepare coins
        coin_map = {coin.rowid: coin for coin in coins}
        coin_cur = coins[0]
        adds = []
        for values in fetch:
            # some sort of caching
            if coin_cur.rowid != values[0]:
                coin_cur = coin_map.get(int(values[0]))
                if coin_cur is None:
                    log.critical(
                        f"No coin with row id:{values[0]} in {coin_map.keys()}")
                    continue
            addr = coin_cur.append_address(*values[1:])
            adds.append(addr)
        for coin in coin_map.values():
            coin.update_balance()
        return adds

    def _read_all_tx(self, adds: List[address.CAddress]) -> List[tx.Transaction]:
        """
        we call this version on start
        """
        if not adds:
            return []
        query = f"""
            SELECT
                {self.wallet_id_column},
                id,
                {self.name_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
                {self.coin_base_column}
            FROM {self.transactions_table};
        """
        with closing(self.__exec(query, )) as c:
            fetch = c.fetchall()
        if not fetch:
            return []
        # prepare
        add_map = {add.rowid: add for add in adds}
        for add in adds:
            add.__txs = []
        add_cur = None
        txs = []
        for values in fetch:
            # some sort of caching
            if not add_cur or add_cur.rowid != values[0]:
                add_cur = add_map.get(int(values[0]))
                if add_cur is None:
                    log.critical(f"No address with row id:{values[0]}")
                    break
            tx_ = tx.Transaction(add_cur)
            tx_.from_args(iter(values[1:]))
            txs.append(tx_)
            add_cur.__txs.append(tx_)
        for add in add_map.values():
            add.add_tx_list(add.__txs)
        return txs

    def _read_all_inputs(self, txs):
        """
        we call this version on start
        """
        if not txs:
            return []
        # we don't need rowID here !!!
        query = f"""
            SELECT
                {self.tx_id_column},
                {self.type_column},
                {self.address_column},
                {self.amount_column},
                {self.output_type_column}
            FROM {self.inputs_table};
        """
        with closing(self.__exec(query, )) as c:
            fetch = c.fetchall()
        if not fetch:
            return []
        # prepare
        tx_map = {tx.rowid: tx for tx in txs}
        for tx in txs:
            tx.__ins = []
        tx_cur = None
        ins = []
        for values in fetch:
            # some sort of caching
            if tx_cur is None or tx_cur.rowid != values[0]:
                tx_cur = tx_map.get(int(values[0]))
                if tx_cur is None:
                    log.critical(f"No tx with row id:{values[0]}")
                    break
            ins.append(
                tx_cur.make_input(iter(values[1:]))
            )
        qt_core.QCoreApplication.processEvents()
        return ins

    def __getattr__(self, attr: str) -> str:
        if attr.endswith("_column") or attr.endswith("_table"):
            return self.__impl.__getattr__(attr)
        raise AttributeError(attr)
