import logging
from typing import Optional, List
import sqlite3 as sql
import sys
from pathlib import Path
# to debug
from ...server import net_cmd

import PySide2.QtCore as qt_core

from .. import address, coins, tx
from . import sqlite_impl

log = logging.getLogger(__name__)


def nmark(number: int) -> str:
    return f"({','.join('?'*number)})"


class DatabaseError(Exception):
    pass


class DbWrapper(sqlite_impl.SqLite):
    """
    Command wrappers here
    """
    DEFAULT_DB_NAME = 'sqlite.db'

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self._save_address_timer: qt_core.QBasicTimer = qt_core.QBasicTimer()
        self._save_address_timer.wallet = None
        self._db_name = None

    def open_db(self, password: bytes, nonce: bytes, db_name: str = None) -> None:
        # assert password, "Not empty password expected"
        assert isinstance(password, bytes)
        assert isinstance(nonce, bytes)
        self._db_name = db_name or self.DEFAULT_DB_NAME
        self.connect_impl(self._db_name, password=password, nonce=nonce)
        self.create_tables()

    def close_db(self) -> None:
        if self._conn:
            self._conn.close()
            log.debug('connection is closed ')
            self._conn = None

    def drop_db(self) -> None:
        self.close_db()
        if self._db_name:
            pth = Path(self._db_name)
            self._db_name = None
            if pth.exists():
                pth.unlink()

    def reset_db(self, password: str) -> None:
        self.drop_db()
        self.open_db(password, self._db_name)

    @classmethod
    def has_db(cls) -> bool:
        return Path(cls._db_name).exists()

    def _add_coin(self, coin: coins.CoinType, read_addresses=False) -> None:
        """
        - insert coin if not exists
        - set rowid for coin
        - read wallets
        """
        name = self(coin.name)
        height = self(coin.height)
        verified_height = self(coin.verified_height)
        offset = self(coin.offset)
        unverified_offset = self(coin.unverified_offset)
        unverified_signature = self(coin.unverified_signature)
        rate = self(coin.rate)
        visible = self(coin.visible)
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
            c = self._exec_(query, (
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
        if coin.rowid is None and c.lastrowid:
            coin.rowid = c.lastrowid
            query = f"""
                SELECT {self.visible_column} FROM {self.coins_table} WHERE id == ?;
            """
            c = self._exec_(query, (coin.rowid,))
            res = c.fetchone()
            coin.visible = res[0]
            c.close()
        else:
            query = f"""
                SELECT id , {self.visible_column} FROM {self.coins_table} WHERE {self.name_column} == ?;
            """
            c = self._exec_(query, (name,))
            res = c.fetchone()
            coin.rowid = res[0]
            coin.visible = res[1]
            c.close()
            log.debug(f"coin exists:{coin} : {res}")
        c.close()
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

            c = self._exec_(query, (
                self(coin.visible),
                self(coin.height),
                self(coin.verified_height),
                self(coin.offset),
                self(coin.unverified_offset),
                self(coin.unverified_signature),
                self(coin.rate),
                coin.rowid,
            ))
            c.close()
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
        c = self._exec_(query, (coin.rowid,))
        fetch = c.fetchall()
        c.close()
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
        c = self._exec_(query, (wallet.rowid,))
        fetch = c.fetchall()
        c.close()
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
                {self.amount_column}
            FROM {self.inputs_table} WHERE {self.tx_id_column} == ?;
        """
        c = self._exec_(query, (tx.rowid,))
        fetch = c.fetchall()
        c.close()
        for values in fetch:
            tx.make_input(iter(values))
        qt_core.QCoreApplication.processEvents()

    def _read_tx_count(self, wallet: address.CAddress) -> None:
        query = f"""
        SELECT Count(*) FROM {self.transactions_table}
        WHERE {self.wallet_id_column} == ?;
        """
        c = self._exec_(query, (wallet.rowid,))
        fetch = c.fetchone()
        c.close()
        return fetch[0]

    def _clear_tx(self, address: address.CAddress) -> None:
        query = f"""
        DELETE FROM {self.transactions_table}
        WHERE {self.wallet_id_column} == ?;
        """
        c = self._exec_(query, (address.rowid,))
        c.close()

    def _remove_tx(self, tx_: tx.Transaction) -> None:
        if tx_.rowid is None:
            query = f"""
            DELETE FROM {self.transactions_table}
            WHERE {self.name_column} == ?;
            """
            c = self._exec_(query, (self(tx_.name),))
        else:
            query = f"""
            DELETE FROM {self.transactions_table}
            WHERE id == ?;
            """
            c = self._exec_(query, (tx_.rowid,))
        c.close()

    def _remove_tx_list(self, tx_list: List[tx.Transaction]) -> None:
        # TODO: optimize
        # may be row ids?
        # tx_hashes = f"({','.join(map(lambda t: self(t.name),tx_list))})"
        # log.warning(f"tx hashes:{tx_hashes}")
        # query = f"""
        # DELETE FROM {self.transactions_table}
        # WHERE {self.name_column} IN ?;
        # """
        # c = self._exec_(query, (tx_list,))
        # c.close()

        for tx_ in tx_list:
            self._remove_tx(tx_)

    def _add_or_save_wallet(self, wallet: address.CAddress, timeout: int = None) -> None:
        if not timeout:
            self._add_or_save_wallet_impl(wallet)
        else:
            if self._save_address_timer.wallet and self._save_address_timer.wallet is not wallet:
                self._add_or_save_wallet_impl(self._save_address_timer.wallet)
            self._save_address_timer.wallet = wallet
            self._save_address_timer.start(timeout, self)

    def _add_or_save_wallet_impl(self, wallet: address.CAddress) -> None:
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
                c = self._exec_(query, (
                    self(wallet.name),
                    wallet.coin.rowid,  # don't encrypt!
                    self(wallet.label, True, "wallet label"),
                    self(wallet.message, True, "wallet message"),
                    self(wallet.created_db_repr),
                    # they're  empty at first place but later not !
                    self(wallet.type),
                    self(wallet.balance),
                    self(wallet.txCount),
                    self(wallet.first_offset),
                    self(wallet.last_offset),
                    self(wallet.export_key(), True, "wallet key"),
                ))
                wallet.rowid = c.lastrowid
                wallet.valid = True
                c.close()

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
                c = self._exec_(query, (
                    self(wallet.label, True, "wallet label"),
                    self(wallet.type),
                    self(wallet.balance),
                    self(wallet.txCount),
                    self(wallet.first_offset),
                    self(wallet.last_offset),
                    wallet.rowid
                ))
                c.close()
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
        c = self._exec_(query, (wallet.rowid,))
        c.close()
        self._clear_tx(wallet)
        log.debug(f"Wallet {wallet} erased from DB")

    def _apply_password(self, password: bytes, nonce: bytes) -> None:
        # why ??
        # self.drop_db()
        self.open_db(password, nonce)
        self._init_actions()

    def _set_meta_entry(self, name: str, value: str, strong: bool = False) -> None:
        """
        if not strong then we shouldn't use password
        """
        name_ = self(name)
        strong = strong or name in ("seed",)
        value_ = self(value, strong, name)
        try:
            # need to have sqlite > 3.22
            query = f"""
            INSERT INTO {self.meta_table} ({self.key_column}, {self.value_column})
            VALUES(?,?)
            ON CONFLICT({self.key_column}) DO UPDATE SET
                {self.value_column}=?
            WHERE {self.key_column} == ?
            """
            c = self._exec_(query, (name_, value_, value_, name_))
        except sql.OperationalError:
            query = f"""
            UPDATE {self.meta_table} SET {self.value_column}=?
            WHERE {self.key_column} == ?;
            """
            c = self._exec_(query, (value_, name_))
            c.close()
            query = f"""
            INSERT INTO {self.meta_table}  ({self.key_column},{self.value_column})
            SELECT ?, ?
            WHERE (Select Changes() = 0);
            """
            c = self._exec_(query, (name_, value_))
        c.close()
        log.debug(
            f"New {'strong' if  strong else ''} meta entry set '{name}'={value}")

    def _get_meta_entry(self, name: str, strong: bool = True) -> Optional[str]:
        name_ = self(name)
        query = f"""
        SELECT  {self.value_column} FROM {self.meta_table} WHERE {self.key_column} = (?)
        """
        c = self._exec_(query, (name_,))
        fetch = c.fetchone()
        c.close()
        if fetch:
            return fetch[0]
        log.debug(f"no meta with name {name_}")

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
            c = self._exec_(query,
                            (
                                self(tx.name),
                                tx.wallet.rowid,
                                self(tx.height),
                                self(tx.time),
                                self(tx.balance),
                                self(tx.fee),
                                self(tx.coin_base),
                            )
                            )
            tx.rowid = c.lastrowid
            c.close()
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
                c = self._exec_(query,
                                (
                                    self(tx.name),
                                    address.rowid,
                                    self(tx.height),
                                    self(tx.time),
                                    self(tx.balance),
                                    self(tx.fee),
                                    self(tx.coin_base),
                                )
                                )
                tx.rowid = c.lastrowid
                c.close()
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
                    log.warn(f"Can't save TX:{ie}")
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
                ({self.address_column},{self.tx_id_column},{self.amount_column},{self.type_column})
                VALUES  {nmark(4)}
            """
            c = self._exec_(query,
                            (
                                self(inp.address),
                                inp.tx.rowid,
                                self(inp.amount),
                                self(inp.out),
                            )
                            )
            c.close()
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
        c = self._exec_(query,)
        fetch = c.fetchall()
        c.close()
        if not fetch:
            for c in coins_:
                self._add_coin(c)
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
        c = self._exec_(query,)
        fetch = c.fetchall()
        c.close()
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
        c = self._exec_(query, )
        fetch = c.fetchall()
        c.close()
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
                {self.amount_column}
            FROM {self.inputs_table};
        """
        c = self._exec_(query, )
        fetch = c.fetchall()
        c.close()
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
            if not tx_cur or tx_cur.rowid != values[0]:
                tx_cur = tx_map.get(int(values[0]))
                if tx_cur is None:
                    log.critical(f"No tx with row id:{values[0]}")
                    break
            ins.append(
                tx_cur.make_input(iter(values[1:]))
            )
        qt_core.QCoreApplication.processEvents()
        return ins
