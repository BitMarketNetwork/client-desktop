from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import bmnclient.config
from . import sqlite_impl
from ..coins.abstract.coin import AbstractCoin
from ..logger import Logger

if TYPE_CHECKING:
    from typing import Dict, List, Sequence, Tuple
    from ..utils.serialize import DeserializedData


def nmark(number: int) -> str:
    return f"({','.join('?' * number)})"


class Database:
    DEFAULT_DB_NAME = str(bmnclient.config.USER_DATABASE_FILE_PATH)

    def __init__(self) -> None:
        super().__init__()
        self._logger = Logger.getClassLogger(__name__, self.__class__)
        self._logger.info("SQLite version: %s", sqlite3.sqlite_version)
        self.__db_name = None
        self.__impl = sqlite_impl.SqLite()
        self._is_loaded = False

    def __getattr__(self, attr: str) -> str:
        if attr.endswith("_column") or attr.endswith("_table"):
            return self.__impl.__getattr__(attr)
        raise AttributeError(attr)

    def open(self) -> None:
        self.__db_name = self.DEFAULT_DB_NAME
        self.__impl.connect_impl(self.__db_name)
        self.__impl.create_tables()

        from ..application import CoreApplication

        coin_list = CoreApplication.instance().coinList
        self.readCoinList(coin_list)

        address_list = self.readCoinAddressList(coin_list)
        self.readCoinTxList(address_list)

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
        try:
            return self.__impl.exec(query, args)
        except sqlite3.DatabaseError as ie:
            self._logger.error("Database error: %s", str(ie))
            return None

    def _encryptDeserializedData(
            self,
            data: DeserializedData) -> DeserializedData:
        for (key, value) in data.items():
            if isinstance(value, (str, int, type(None))):
                data[key] = self.__impl(value)
        return data

    def appendCoin(self, coin: AbstractCoin) -> bool:
        data = self._encryptDeserializedData(coin.serialize())
        query = " ".join((
            f"INSERT OR IGNORE INTO {self.coins_table} (",
            f"{self.name_column},",
            f"{self.visible_column},",
            f"{self.height_column},",
            f"{self.verified_height_column},",
            f"{self.offset_column},",
            f"{self.unverified_offset_column},",
            f"{self.unverified_hash_column}",
            f") VALUES {nmark(7)}"
        ))
        cursor = self.execute(query, (
            data["name"],
            self.__impl(1),
            data["height"],
            data["verified_height"],
            data["offset"],
            data["unverified_offset"],
            data["unverified_hash"]
        ))
        if cursor is None:
            return False
        row_id = cursor.lastrowid
        cursor.close()

        if coin.rowId is None and row_id is not None:
            coin.rowId = row_id
            return True

        query = " ".join((
            f"SELECT",
            f"id",
            f"FROM {self.coins_table}",
            f"WHERE {self.name_column}==? LIMIT 1"
        ))
        cursor = self.execute(query, (data["name"],))
        if cursor is None:
            return False
        result = cursor.fetchone()
        coin.rowId = int(result[0])
        cursor.close()
        return True

    def readCoinList(self, coin_list: Sequence[AbstractCoin]) -> bool:
        query = " ".join((
            f"SELECT",
            f"id,"                                # 0
            f"{self.name_column},",               # 1
            f"{self.height_column},",             # 2
            f"{self.verified_height_column},",    # 3
            f"{self.offset_column},",             # 4
            f"{self.unverified_offset_column},",  # 5
            f"{self.unverified_hash_column}",     # 6
            f"FROM {self.coins_table}"
        ))
        cursor = self.execute(query)
        if cursor is None:
            return False
        fetch = cursor.fetchall()
        cursor.close()

        if not fetch:
            for coin in coin_list:
                self.appendCoin(coin)
            return True

        for value in fetch:
            coin_name = str(value[1])
            for coin in coin_list:
                if coin.name != coin_name:
                    continue

                coin.rowId = int(value[0])
                if coin.height < int(value[2]):
                    coin.deserialize(
                        coin,
                        name=coin_name,
                        height=int(value[2]),
                        verified_height=int(value[3]),
                        offset=str(value[4]),
                        unverified_offset=str(value[5]),
                        unverified_hash=str(value[6]))
                else:
                    self._logger.debug(f"Saved coin {coin_name} was skipped.")
                    self.updateCoin(coin)
        return True

    def updateCoin(self, coin: AbstractCoin) -> bool:
        if not coin.rowId:
            self._logger.error("No coin row")
            return False

        data = self._encryptDeserializedData(coin.serialize())
        query = " ".join((
            f"UPDATE {self.coins_table} SET",
            f"{self.visible_column}=?,",            # 0
            f"{self.height_column}=?,",             # 1
            f"{self.verified_height_column}=?,",    # 2
            f"{self.offset_column}=?,",             # 3
            f"{self.unverified_offset_column}=?,",  # 4
            f"{self.unverified_hash_column}=?",     # 5
            f"WHERE id=?"                           # 6
        ))
        cursor = self.execute(query, (
            self.__impl(1),
            data["height"],
            data["verified_height"],
            data["offset"],
            data["unverified_offset"],
            data["unverified_hash"],
            coin.rowId
        ))
        if cursor is None:
            return False
        cursor.close()
        return True

    def updateCoinAddress(self, address: AbstractCoin.Address) -> bool:
        assert address.coin.rowId is not None
        data = self._encryptDeserializedData(address.serialize())

        if address.rowId is None:
            query = " ".join((
                f"INSERT INTO {self.addresses_table} (",
                f"{self.address_column},",                # 0
                f"{self.coin_id_column},",                # 1
                f"{self.label_column},",                  # 2
                f"{self.message_column},",                # 3
                f"{self.created_column},",                # 4
                f"{self.type_column},",                   # 5
                f"{self.amount_column},",                 # 6
                f"{self.tx_count_column},",               # 7
                f"{self.first_offset_column},",           # 8
                f"{self.last_offset_column},",            # 9
                f"{self.key_column}",                     # 10
                f") VALUES {nmark(11)}"
            ))
            cursor = self.execute(query, (
                data["name"],
                address.coin.rowId,
                data["label"],
                data["comment"],
                self.__impl(0),
                "",
                data["amount"],
                data["tx_count"],
                data["history_first_offset"],
                data["history_last_offset"],
                self.__impl(address.exportPrivateKey(), True, "wallet key"),
            ))
            if cursor is None:
                return False
            address.rowId = cursor.lastrowid
            cursor.close()
        else:
            query = " ".join((
                f"UPDATE {self.addresses_table} SET",
                f"{self.label_column}=?,",             # 0
                f"{self.type_column}=?,",              # 1
                f"{self.amount_column}=?,",            # 2
                f"{self.tx_count_column}=?,",          # 3
                f"{self.first_offset_column}=?,",      # 4
                f"{self.last_offset_column}=?",        # 5
                f"WHERE id=?"                          # 6
            ))
            cursor = self.execute(query, (
                data["label"],
                "",
                data["amount"],
                data["tx_count"],
                data["history_first_offset"],
                data["history_last_offset"],
                address.rowId
            ))
            if cursor is None:
                return False
            cursor.close()
        return True

    def readCoinAddressList(
            self,
            coin_list: Sequence[AbstractCoin]) \
            -> List[AbstractCoin.Address]:
        query = " ".join((
            f"SELECT",
            f"{self.coin_id_column},",       # 0
            f"{self.address_column},",       # 1
            f"id,",                          # 2
            f"{self.label_column},",         # 3
            f"{self.message_column},",       # 4
            f"{self.created_column},",       # 5
            f"{self.type_column},",          # 6
            f"{self.amount_column},",        # 7
            f"{self.tx_count_column},",      # 8
            f"{self.first_offset_column},",  # 9
            f"{self.last_offset_column},",   # 10
            f"{self.key_column}",            # 11
            f"FROM {self.addresses_table}"
        ))
        cursor = self.execute(query)
        if cursor is None:
            return []
        fetch = cursor.fetchall()
        cursor.close()

        coin_map = {c.rowId: c for c in coin_list}
        coin = coin_list[0]
        address_list = []

        for value in fetch:
            coin_row_id = int(value[0])
            if coin.rowId != coin_row_id:
                coin = coin_map.get(coin_row_id)
                if coin is None:
                    continue

            address = coin.Address.deserialize(
                coin,
                name=str(value[1]),
                private_key=str(value[11]),
                amount=int(value[7]),
                tx_count=int(value[8]),
                label=str(value[3]),
                comment=str(value[4]),
                history_first_offset=str(value[9]),
                history_last_offset=str(value[10]))
            if address is not None:
                address.rowId = int(value[2])
                coin.appendAddress(address)
                address_list.append(address)

        for coin in coin_list:
            coin.refreshAmount()
        return address_list

    def updateCoinAddressTx(
            self,
            address: AbstractCoin.Address,
            tx: AbstractCoin.Tx) -> bool:
        assert address.rowId is not None
        data = self._encryptDeserializedData(tx.serialize())
        query = " ".join((
            f"INSERT  INTO {self.transactions_table} (",
            f"{self.name_column},",                       # 0
            f"{self.address_id_column},",                 # 1
            f"{self.height_column},",                     # 2
            f"{self.time_column},",                       # 3
            f"{self.amount_column},",                     # 4
            f"{self.fee_amount_column},",                 # 5
            f"{self.coinbase_column}",                    # 6
            f") VALUES {nmark(7)}"
        ))
        cursor = self.execute(query, (
            data["name"],
            address.rowId,
            data["height"],
            data["time"],
            data["amount"],
            data["fee_amount"],
            data["coinbase"],
        ))
        if cursor is None:
            return False
        tx.rowId = cursor.lastrowid
        cursor.close()

        for io_data in data["input_list"]:
            self._writeCoinTxIo(
                tx.rowId,
                self._encryptDeserializedData(io_data),
                True)
        for io_data in data["output_list"]:
            self._writeCoinTxIo(
                tx.rowId,
                self._encryptDeserializedData(io_data),
                False)
        return True

    def readCoinTxList(self, address_list: List[AbstractCoin.Address]) -> bool:
        if not address_list:
            return True

        query = " ".join((
            f"SELECT",
            f"{self.address_id_column},",      # 0
            f"id,",                            # 1
            f"{self.name_column},",            # 2
            f"{self.height_column},",          # 3
            f"{self.time_column},",            # 4
            f"{self.amount_column},",          # 5
            f"{self.fee_amount_column},",      # 6
            f"{self.coinbase_column}",         # 7
            f"FROM {self.transactions_table}"
        ))
        cursor = self.execute(query)
        if cursor is None:
            return False
        fetch = cursor.fetchall()
        cursor.close()

        tx_input_list, tx_output_list = self._readCoinTxIo()

        address_map = {a.rowId: a for a in address_list}
        address = None

        for value in fetch:
            address_row_id = int(value[0])
            if not address or address.rowId != address_row_id:
                address = address_map.get(address_row_id)
                if address is None:
                    continue

            tx_row_id = int(value[1])
            tx = address.coin.Tx.deserialize(
                address.coin,
                name=str(value[2]),
                height=int(value[3]),
                time=int(value[4]),
                amount=int(value[5]),
                fee_amount=int(value[6]),
                coinbase=int(value[7]),
                input_list=tx_input_list.get(tx_row_id, []),
                output_list=tx_output_list.get(tx_row_id, []),
            )
            if tx is not None:
                tx.rowId = tx_row_id
                address.appendTx(tx)
        return True

    def _writeCoinTxIo(
            self,
            tx_row_id: int,
            data: DeserializedData,
            is_input: bool) -> bool:
        query = " ".join((
            f"INSERT INTO {self.inputs_table} (",
            f"{self.address_column},",             # 0
            f"{self.tx_id_column},",               # 1
            f"{self.amount_column},",              # 2
            f"{self.type_column},",                # 3
            f"{self.output_type_column}",          # 4
            f") VALUES {nmark(5)}"
        ))
        cursor = self.execute(query, (
            data["address_name"],
            tx_row_id,
            data["amount"],
            self.__impl(1 if is_input else 0),
            data["output_type"]
        ))
        if cursor is None:
            return False
        cursor.close()
        return True

    def _readCoinTxIo(self) \
            -> Tuple[Dict[int, DeserializedData], Dict[int, DeserializedData]]:
        query = " ".join((
            f"SELECT",
            f"{self.tx_id_column},",       # 0
            f"{self.type_column},",        # 1
            f"{self.address_column},",     # 2
            f"{self.amount_column},",      # 3
            f"{self.output_type_column}",  # 4
            f"FROM {self.inputs_table}",
        ))
        cursor = self.execute(query)
        if cursor is None:
            return {}, {}
        fetch = cursor.fetchall()
        cursor.close()

        result_input = {}
        result_output = {}
        for value in fetch:
            tx_row_id = int(value[0])
            is_input = int(value[1]) > 0
            data = {
                "output_type": str(value[4]),
                "address_name": str(value[2]),
                "amount": int(value[3])
            }
            if is_input:
                result_input.setdefault(tx_row_id, []).append(data)
            else:
                result_output.setdefault(tx_row_id, []).append(data)
        return result_input, result_output
