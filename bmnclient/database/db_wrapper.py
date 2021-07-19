from __future__ import annotations

from typing import TYPE_CHECKING

from ..coins.abstract.coin import AbstractCoin

if TYPE_CHECKING:
    from typing import Dict, List, Sequence, Tuple
    from ..utils.serialize import DeserializedDict


class Database:
    def open(self) -> None:
        self.readCoinTxList(address_list)

    def updateCoinAddressTx(
            self,
            address: AbstractCoin.Address,
            tx: AbstractCoin.Tx) -> bool:
        assert address.rowId is not None
        data = self._encryptDeserializedData(tx.serialize())

        if tx.rowId is None:
            query = " ".join((
                f"INSERT INTO {self.transactions_table} (",
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
        else:
            query = " ".join((
                f"UPDATE {self.transactions_table} SET",
                f"{self.height_column}=?,",               # 0
                f"{self.time_column}=?",                  # 1
                f"WHERE id=?"
            ))
            cursor = self.execute(query, (
                data["height"],
                data["time"],
                tx.rowId
            ))
            if cursor is None:
                return False
            cursor.close()
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
            data: DeserializedDict,
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
            -> Tuple[Dict[int, DeserializedDict], Dict[int, DeserializedDict]]:
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
