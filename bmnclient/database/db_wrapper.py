from __future__ import annotations

import logging
import sqlite3 as sql
import sys
from contextlib import closing
from pathlib import Path
from typing import List, Tuple

import PySide2.QtCore as qt_core

import bmnclient.config
from . import sqlite_impl
from ..coins.abstract.coin import AbstractCoin
from ..wallet import coins

log = logging.getLogger(__name__)


def nmark(number: int) -> str:
    return f"({','.join('?' * number)})"


class Database:
    DEFAULT_DB_NAME = str(bmnclient.config.USER_DATABASE_FILE_PATH)

    def __init__(self) -> None:
        super().__init__()
        log.info(f"SQLite version {sql.sqlite_version}")
        self.__db_name = None
        self.__impl = sqlite_impl.SqLite()
        self._is_loaded = False

    def open(self) -> None:
        self.__db_name = self.DEFAULT_DB_NAME
        self.__impl.connect_impl(self.__db_name)
        self.__impl.create_tables()

        from ..application import CoreApplication

        coin_list = CoreApplication.instance().coinList
        self._read_all_coins(coin_list)

        address_list = self._read_all_addresses(coin_list)
        self._read_all_tx(address_list)

        self._is_loaded = True

    @property
    def isLoaded(self) -> bool:
        return self._is_loaded

    def close(self) -> None:
        self._is_loaded = False
        self.__impl.close()

    def remove(self) -> None:
        self.close()
        if self.__db_name:
            pth = Path(self.__db_name)
            self.__db_name = None
            if pth.exists():
                pth.unlink()

    def execute(self, query: str, args: tuple = ()):
        return self.__impl.exec(query, args)

    def _add_coin(self, coin: coins.CoinType) -> None:
        table = coin.serialize()
        for (key, value) in table.items():
            if not isinstance(table[key], list):
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
                table["name"],
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
            with closing(self.execute(query, (coin.rowId,))) as c:
                res = c.fetchone()
                coin.visible = res[0]
        else:
            query = f"""
                SELECT id , {self.visible_column} FROM {self.coins_table} WHERE {self.name_column} == ?;
            """
            with closing(self.execute(query, (table["name"],))) as c:
                res = c.fetchone()
                coin.rowId = res[0]
                coin.visible = res[1]

    def writeCoin(self, coin: coins.CoinType) -> None:
        if not coin.rowId:
            log.error("No coin row")
            return

        table = coin.serialize()
        for (key, value) in table.items():
            if not isinstance(table[key], list):
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

            with closing(self.execute(query, (
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
            log.error("DB integrity: %s (%s)", ie, coin.name)

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
        FROM {self.addresses_table} WHERE {self.coin_id_column} == ?;
        """
        with closing(self.execute(query, (coin.rowId,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            wallet = CAddress(values[0], c)
            wallet.create()
            wallet.from_args(iter(values[1:]))
            c.appendAddress(wallet)
            self._read_tx_list(wallet)
            wallet.valid = True
            ##
            # self.update_wallet.emit(wallet)

    def _read_tx_list(self, wallet: AbstractCoin.Address) -> None:
        query = f"""
            SELECT
                id,
                {self.name_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
                {self.status_column}
            FROM {self.transactions_table} WHERE {self.address_id_column} == ?;
        """
        with closing(self.execute(query, (wallet.rowId,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            qt_core.QCoreApplication.processEvents()
            tx = AbstractTx(wallet)
            tx.from_args(iter(values))
            self._read_input_list(tx)
            wallet.appendTx(tx)

    def _read_input_list(self, tx: AbstractCoin.Tx) -> None:
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
        with closing(self.execute(query, (tx.rowId,))) as c:
            fetch = c.fetchall()
        for values in fetch:
            tx.make_input(iter(values))
        qt_core.QCoreApplication.processEvents()

    def writeCoinAddress(self, address: AbstractCoin.Address) -> None:
        assert address.coin.rowId

        table = address.serialize()
        for (key, value) in table.items():
            if not isinstance(table[key], list):
                table[key] = self.__impl(value)

        if address.rowId is None:
            query = f"""
            INSERT INTO {self.addresses_table} (
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
                {self.key_column})
                VALUES  {nmark(11)}
            """
            try:
                with closing(self.execute(query, (
                    table["name"],
                    address.coin.rowId,  # don't encrypt!
                    table["label"],
                    table["comment"],
                    self.__impl(0),
                    "",
                    table["amount"],
                    table["tx_count"],
                    table["history_first_offset"],
                    table["history_last_offset"],
                    self.__impl(address.exportPrivateKey(), True, "wallet key"),
                ))) as c:
                    address.rowId = c.lastrowid

            except sql.IntegrityError as ie:
                log.warning(f"Can't add wallet:'{address.name}' => '{ie}'")
                # it can happen if user address_list existing address
                # sys.exit(1)
            """
            we don't put some fields in update scope cause we don't expect them being changed
            """
        else:
            log.debug("saving wallet info %s", address.name)
            query = f"""
            UPDATE {self.addresses_table} SET
                {self.label_column} = ?,
                {self.type_column} = ?,
                {self.amount_column} = ?,
                {self.tx_count_column} = ?,
                {self.first_offset_column} = ?,
                {self.last_offset_column} = ?
            WHERE id = ?
            """

            try:
                with closing(self.execute(query, (
                    table["label"],
                    "",
                    table["amount"],
                    table["tx_count"],
                    table["history_first_offset"],
                    table["history_last_offset"],
                    address.rowId
                ))):
                    pass
            except sql.IntegrityError as ie:
                log.error(f"DB integrity: {ie} for {address.name}")
            except sql.InterfaceError as ie:
                log.error(f"DB integrity: {ie}  for {address.name}")

    def writeCoinTx(self, tx: AbstractCoin.Tx) -> None:
        table = tx.serialize()
        for (key, value) in table.items():
            if not isinstance(value, list):
                table[key] = self.__impl(value)

        try:
            query = f"""
            INSERT  INTO {self.transactions_table} (
                {self.name_column},
                {self.address_id_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_amount_column},
                {self.coinbase_column}
                ) VALUES  {nmark(7)}
            """
            assert tx.address.rowId is not None
            with closing(self.execute(query, (
                    table["name"],
                    tx.address.rowId,
                    table["height"],
                    table["time"],
                    table["amount"],
                    table["fee_amount"],
                    table["coinbase"],
            ))) as c:
                tx.rowId = c.lastrowid

            # TODO read from table
            for item in tx.inputList:
                self.writeCoinTxIo(tx, item, False)
            for item in tx.outputList:
                self.writeCoinTxIo(tx, item, True)
        except sql.IntegrityError as ie:
            # TODO: adjust query instead
            if str(ie).find('UNIQUE') < 0:
                log.fatal("TX exists: %s (%s)", tx.name, ie)
                sys.exit(1)
            else:
                pass
        except AssertionError:
            sys.exit(1)

    def writeCoinTxIo(self, tx: AbstractCoin.Tx, inp, out) -> None:
        table = inp.serialize()["address"]
        for (key, value) in table.items():
            if not isinstance(table[key], list):
                table[key] = self.__impl(value)

        try:
            query = f"""
            INSERT INTO {self.inputs_table} (
                    {self.address_column},
                    {self.tx_id_column},
                    {self.amount_column},
                    {self.type_column},
                    {self.output_type_column})
                VALUES {nmark(5)}
            """
            with closing(self.execute(query, (
                table["name"],
                tx.rowId,
                table["amount"],
                self.__impl(out),
                "",
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
                {self.unverified_hash_column}
                FROM {self.coins_table};
        """
        with closing(self.execute(query)) as c:
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
            usig
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
                log.warning(f"saved coin {name} isn't found ")

    def _read_all_addresses(self, coins: coins.CoinType) -> AbstractCoin.Address:
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
        FROM {self.addresses_table}
        """
        with closing(self.execute(query,)) as c:
            fetch = c.fetchall()
        # prepare coins
        coin_map = {coin.rowId: coin for coin in coins}
        coin_cur = coins[0]
        address_list = []
        for values in fetch:
            # some sort of caching
            if coin_cur.rowId != values[0]:
                coin_cur = coin_map.get(int(values[0]))
                if coin_cur is None:
                    log.critical(
                        f"No coin with row id:{values[0]} in {coin_map.keys()}")
                    continue
            addr = CAddress(coin_cur, name=values[1])
            addr.create()
            addr.from_args(iter(values[2:]))
            coin_cur.appendAddress(addr)
            address_list.append(addr)
        for coin in coin_map.values():
            coin.refreshAmount()
        return address_list

    def _read_all_tx(self, address_list: List[AbstractCoin.Address]) -> None:
        if not address_list:
            return []

        tx_input, tx_output = self._read_all_tx_io()

        query = f"""SELECT
                {self.address_id_column},
                id,
                {self.name_column},
                {self.height_column},
                {self.time_column},
                {self.amount_column},
                {self.fee_column},
                {self.coinbase_column}
            FROM {self.transactions_table}"""
        with closing(self.execute(query)) as c:
            fetch = c.fetchall()
        if not fetch:
            return

        # prepare
        address_map = {address.rowId: address for address in address_list}
        add_cur = None
        for values in fetch:
            if not add_cur or add_cur.rowId != values[0]:
                add_cur = address_map.get(int(values[0]))
                if add_cur is None:
                    log.critical(f"No address with row id:{values[0]}")
                    break
            arg_iter = iter(values[1:])
            _rowid = next(arg_iter)
            value = {
                "name": next(arg_iter),
                "height": next(arg_iter),
                "time": next(arg_iter),
                "amount": next(arg_iter),
                "fee": next(arg_iter),
                "coinbase": next(arg_iter),
                "input_list": tx_input.get(_rowid, []),
                "output_list": tx_output.get(_rowid, [])
            }

            tx = AbstractTx.deserialize(add_cur, **value)
            tx.rowId = _rowid
            add_cur.appendTx(tx)

    def _read_all_tx_io(self) -> Tuple[dict, dict]:
        query = f"""SELECT
            {self.tx_id_column},
            {self.type_column},
            {self.address_column},
            {self.amount_column},
            {self.output_type_column}
            FROM {self.inputs_table}"""
        with closing(self.execute(query)) as c:
            fetch = c.fetchall()
        if not fetch:
            return {}, {}

        result_input = {}
        result_output = {}
        for values in fetch:
            value = {
                "output_type": values[4],
                "address_type": "",  # TODO
                "address_name": values[2],
                "amount": values[3]
            }
            tx_row_id = values[0]
            if values[1]:
                if tx_row_id not in result_output:
                    result_output[tx_row_id] = []
                result_output[tx_row_id].append(value)
            else:
                if tx_row_id not in result_input:
                    result_input[tx_row_id] = []
                result_input[tx_row_id].append(value)

        return result_input, result_output

    def __getattr__(self, attr: str) -> str:
        if attr.endswith("_column") or attr.endswith("_table"):
            return self.__impl.__getattr__(attr)
        raise AttributeError(attr)
