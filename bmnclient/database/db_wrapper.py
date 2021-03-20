from __future__ import annotations

import logging
import sqlite3 as sql
import sys
from contextlib import closing
from pathlib import Path
from typing import List

import PySide2.QtCore as qt_core

import bmnclient.config
from . import sqlite_impl
from ..server import net_cmd
from ..wallet import coins
from ..wallet.address import CAddress
from ..wallet.tx import Transaction

log = logging.getLogger(__name__)


def nmark(number: int) -> str:
    return f"({','.join('?'*number)})"


class DbWrapper:
    DEFAULT_DB_NAME = str(bmnclient.config.USER_DATABASE_FILE_PATH)

    def __init__(self) -> None:
        super().__init__()
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
        table = coin.serialize()
        for (key, value) in table.items():
            table[key] = self.__impl(value)

        try:
            query = f"""
            INSERT OR IGNORE INTO {self.coins_table} (
                    {self.name_column},
                    {self.visible_column},
                    {self.height_column},
                    {self.verified_height_column},
                    {self.offset_column},
                    {self.unverified_offset_column},
                    {self.unverified_hash_column})
                VALUES  {nmark(7)}
            """
            cursor = self.__impl.exec(query, (
                table["short_name"],
                self.__impl(1),  # TODO
                table["height"],
                table["verified_height"],
                table["offset"],
                table["unverified_offset"],
                table["unverified_hash"]
            ))
        except sql.IntegrityError as ie:
            log.error("DB integrity: %s (%s)", ie, coin)
            return

        if coin.rowId is None and cursor.lastrowid:
            coin.rowId = cursor.lastrowid
            cursor.close()

            query = f"SELECT {self.visible_column} FROM {self.coins_table} WHERE id == ?"
            with closing(self.__exec(query, (coin.rowId,))) as c:
                res = c.fetchone()
                coin.visible = res[0]
        else:
            query = f"""
                SELECT id , {self.visible_column} FROM {self.coins_table} WHERE {self.name_column} == ?;
            """
            with closing(self.__exec(query, (table["short_name"],))) as c:
                res = c.fetchone()
                coin.rowId = res[0]
                coin.visible = res[1]

        if read_addresses:
            self._read_address_list(coin)
        coin.refreshAmount()

    def _update_coin(self, coin: coins.CoinType) -> None:
        if not coin.rowId:
            log.error("No coin row")
            return

        table = coin.serialize()
        for (key, value) in table.items():
            table[key] = self.__impl(value)

        try:
            query = f"""
            UPDATE {self.coins_table} SET
                {self.visible_column} = ?,
                {self.height_column} = ?,
                {self.verified_height_column} = ?,
                {self.offset_column} = ?,
                {self.unverified_offset_column} = ?,
                {self.unverified_hash_column} = ?
                WHERE id = ?;
            """

            with closing(self.__exec(query, (
                self.__impl(1),  # TODO
                table["height"],
                table["verified_height"],
                table["offset"],
                table["unverified_offset"],
                table["unverified_hash"],
                coin.rowId
            ))):
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
            {self.amount_column},
            {self.tx_count_column},
            {self.first_offset_column},
            {self.last_offset_column},
            {self.key_column}
        FROM {self.wallets_table} WHERE {self.coin_id_column} == ?;
        """
        with closing(self.__exec(query, (coin.rowId,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            wallet = address.CAddress(values[0], c)
            wallet.create()
            wallet.from_args(iter(values[1:]))
            c.appendAddress(wallet)
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
        with closing(self.__exec(query, (wallet.rowId,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            qt_core.QCoreApplication.processEvents()
            tx = Transaction(wallet)
            tx.from_args(iter(values))
            self._read_input_list(tx)
            wallet.appendTx(tx)

    def _read_input_list(self, tx: Transaction) -> None:
        """
        and outputs too of course
        """
        assert tx.rowId
        query = f"""
            SELECT
                {self.type_column},
                {self.address_column},
                {self.amount_column},
                {self.output_type_column}
            FROM {self.inputs_table} WHERE {self.tx_id_column} == ?;
        """
        with closing(self.__exec(query, (tx.rowId,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            tx.make_input(iter(values))
        qt_core.QCoreApplication.processEvents()

    def _read_tx_count(self, wallet: address.CAddress) -> None:
        query = f"""
        SELECT Count(*) FROM {self.transactions_table}
        WHERE {self.wallet_id_column} == ?;
        """
        with closing(self._exec_(query, (wallet.rowId,))) as c:
            fetch = c.fetchone()
        return fetch[0]

    def _clear_tx(self, address: address.CAddress) -> None:
        query = f"""
        DELETE FROM {self.transactions_table}
        WHERE {self.wallet_id_column} == ?;
        """
        with closing(self.__exec(query, (address.rowId,))):
            pass

    def _remove_tx(self, tx: Transaction) -> None:
        if tx.rowId is None:
            query = f"""
            DELETE FROM {self.transactions_table}
            WHERE {self.name_column} == ?;
            """
            with closing(self.__exec(query, (self.__impl(tx.name),))):
                pass
        else:
            query = f"""
            DELETE FROM {self.transactions_table}
            WHERE id == ?;
            """
            with closing(self.__exec(query, (self.__impl(tx.rowId),))):
                pass

    def _remove_tx_list(self, tx_list: List[Transaction]) -> None:
        # TODO: optimize
        # may be row ids?
        # tx_hashes = f"({','.join(map(lambda t: self.__impl(t.name),tx_list))})"
        # log.warning(f"tx hashes:{tx_hashes}")
        # query = f"""
        # DELETE FROM {self.transactions_table}
        # WHERE {self.name_column} IN ?;
        # """
        # self._exec_(query, (tx_list,))

        for tx in tx_list:
            self._remove_tx(tx)

    def _add_or_save_wallet(self, wallet: address.CAddress, timeout: int = None) -> None:
        if not timeout:
            self._add_or_save_wallet_impl(wallet)
        else:
            if self._save_address_timer.wallet and self._save_address_timer.wallet is not wallet:
                self._add_or_save_wallet_impl(self._save_address_timer.wallet)
            self._save_address_timer.wallet = wallet
            self._save_address_timer.start(timeout, self)

    def _add_or_save_wallet_impl(self, wallet: address.CAddress) -> None:
        assert wallet.coin.rowId
        if wallet.rowId is None:
            query = f"""
            INSERT  INTO {self.wallets_table}
                (
                    {self.address_column},
                    {self.coin_id_column},
                    {self.label_column},
                    {self.message_column},
                    {self.created_column},
                    {self.type_column},
                    {self.amount_column},
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
                    wallet.coin.rowId,  # don't encrypt!
                    self.__impl(wallet.label, True, "wallet label"),
                    self.__impl(wallet.message, True, "wallet message"),
                    self.__impl(wallet.created_db_repr),
                    # they're  empty at first place but later not !
                    self.__impl(wallet.type),
                    self.__impl(wallet.amount),
                    self.__impl(wallet.txCount),
                    self.__impl(wallet.first_offset),
                    self.__impl(wallet.last_offset),
                    self.__impl(wallet.export_key(), True, "wallet key"),
                ))) as c:
                    wallet.rowId = c.lastrowid
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
                {self.amount_column} = ?,
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
                    self.__impl(wallet.amount),
                    self.__impl(wallet.txCount),
                    self.__impl(wallet.first_offset),
                    self.__impl(wallet.last_offset),
                    wallet.rowId
                ))):
                    pass
            except sql.IntegrityError as ie:
                log.error(f"DB integrity: {ie} for {wallet}")
            except sql.InterfaceError as ie:
                log.error(f"DB integrity: {ie}  for {wallet}")

    def _erase_wallet(self, wallet: address.CAddress) -> None:
        assert wallet.rowId
        query = f"""
            DELETE FROM {self.wallets_table}
            WHERE id == ?
        """
        with closing(self.__exec(query, (wallet.rowId,))):
            pass
        self._clear_tx(wallet)
        log.debug(f"Wallet {wallet} erased from DB")

    def _apply_password(self) -> None:
        self.open_db()
        self._init_actions()

    def _write_transaction(self, tx: Transaction) -> None:
        try:
            query = f"""
            INSERT  INTO {self.transactions_table}
                ({self.name_column},
                {self.wallet_id_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
                {self.coinbase_column}
                ) VALUES  {nmark(7)}
            """
            assert tx.wallet.rowId is not None
            with closing(self.__exec(query,
                                     (
                                         self.__impl(tx.name),
                                         tx.wallet.rowId,
                                         self.__impl(tx.height),
                                         self.__impl(tx.time),
                                         self.__impl(tx.amount),
                                         self.__impl(tx.fee),
                                         self.__impl(tx.coinbase),
                                     ))) as c:
                tx.rowId = c.lastrowid
            # make it in try block ( we don't need inputs withot tx )
            # inputs
            for inp in tx.inputs:
                self._write_input(tx, inp, False)
            for out in tx.outputs:
                self._write_input(tx, out, True)

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
        assert address.rowId is not None
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
                    {self.coinbase_column}
                    ) VALUES  {nmark(7)}
                """
                with closing(self.__exec(query,
                                         (
                                             self.__impl(tx.name),
                                             address.rowId,
                                             self.__impl(tx.height),
                                             self.__impl(tx.time),
                                             self.__impl(tx.amount),
                                             self.__impl(tx.fee),
                                             self.__impl(tx.coinbase),
                                         ))) as c:
                    tx.rowId = c.lastrowid
                # make it in try block ( we don't need inputs withot tx )
                # inputs
                for inp in tx.inputs:
                    self._write_input(tx, inp, False)
                for out in tx.outputs:
                    self._write_input(tx, out, True)

            except sql.IntegrityError as ie:
                if str(ie).find('UNIQUE') < 0:
                    log.fatal("TX exists: %s (%s)", tx, ie)
                    sys.exit(1)
                else:
                    log.debug(f"Can't save TX:{ie}")
                    pass
            except AssertionError:
                sys.exit(1)

    def _write_input(self, tx: Transaction, inp, out) -> None:
        try:
            query = f"""
            INSERT INTO {self.inputs_table}
                ({self.address_column},{self.tx_id_column},{self.amount_column},{self.type_column},{self.output_type_column})
                VALUES  {nmark(5)}
            """
            with closing(self.__exec(query,
                                     (
                                         self.__impl(inp.name),
                                         tx.rowId,
                                         self.__impl(inp.amount),
                                         self.__impl(out),
                                         self.__impl(''),
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
                {self.unverified_hash_column},
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
            rowId,
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
                coin.rowId = rowId
                coin.visible = visible
                coin.offset = offset
                coin.verifiedHeight = vheight
                coin.unverifiedOffset = uoffset
                coin.unverifiedHash = usig
                # TODO coin.fiatRate = FiatRate(rate, UsdFiatCurrency)
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
            {self.amount_column},
            {self.tx_count_column},
            {self.first_offset_column},
            {self.last_offset_column},
            {self.key_column}
        FROM {self.wallets_table}
        """
        with closing(self.__exec(query,)) as c:
            fetch = c.fetchall()
        # prepare coins
        coin_map = {coin.rowId: coin for coin in coins}
        coin_cur = coins[0]
        adds = []
        for values in fetch:
            # some sort of caching
            if coin_cur.rowId != values[0]:
                coin_cur = coin_map.get(int(values[0]))
                if coin_cur is None:
                    log.critical(
                        f"No coin with row id:{values[0]} in {coin_map.keys()}")
                    continue
            addr = address.CAddress(values[1], coin_cur)
            addr.create()
            addr.from_args(iter(values[2:]))
            coin_cur.appendAddress(addr)
            adds.append(addr)
        for coin in coin_map.values():
            coin.refreshAmount()
        return adds

    def _read_all_tx(self, adds: List[address.CAddress]) -> List[Transaction]:
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
                {self.coinbase_column}
            FROM {self.transactions_table};
        """
        with closing(self.__exec(query, )) as c:
            fetch = c.fetchall()
        if not fetch:
            return []
        # prepare
        add_map = {add.rowId: add for add in adds}
        for add in adds:
            add.__txs = []
        add_cur = None
        txs = []
        for values in fetch:
            # some sort of caching
            if not add_cur or add_cur.rowId != values[0]:
                add_cur = add_map.get(int(values[0]))
                if add_cur is None:
                    log.critical(f"No address with row id:{values[0]}")
                    break
            tx = Transaction(add_cur)
            tx.from_args(iter(values[1:]))
            txs.append(tx)
            add_cur.__txs.append(tx)
        for add in add_map.values():
            for tx in add.__txs:
                add.appendTx(tx)
        return txs

    def _read_all_tx_io(self) -> dict:
        query = f"""SELECT
            {self.tx_id_column},
            {self.type_column},
            {self.address_column},
            {self.amount_column},
            {self.output_type_column}
            FROM {self.inputs_table}"""
        with closing(self.__exec(query)) as c:
            fetch = c.fetchall()
        if not fetch:
            return {}

        result = {}
        for values in fetch:
            tx_row_id = values[0]
            if tx_row_id not in result:
                result[tx_row_id] = []
            result[tx_row_id].append({
                "type": values[1],  # TODO
                "output_type": values[4],
                "address_type": "",  # TODO
                "address_name": values[2],
                "amount": values[3]
            })
        return result

    def __getattr__(self, attr: str) -> str:
        if attr.endswith("_column") or attr.endswith("_table"):
            return self.__impl.__getattr__(attr)
        raise AttributeError(attr)
