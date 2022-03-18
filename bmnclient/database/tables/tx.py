from __future__ import annotations

from typing import TYPE_CHECKING

from .table import AbstractTable, Column, ColumnEnum, ColumnValue, SortOrder
from ...utils.class_property import classproperty

if TYPE_CHECKING:
    from typing import Any, Dict, Final, List, Optional, Tuple
    from .. import Cursor
    from ...coins.abstract import Coin


class TxListTable(AbstractTable, name="transactions"):
    class ColumnEnum(ColumnEnum):
        ROW_ID: Final = ()
        COIN_ROW_ID: Final = (
            "coin_row_id",
            "INTEGER NOT NULL")

        NAME: Final = (
            "name",
            "TEXT NOT NULL")
        HEIGHT: Final = (
            "height",
            "INTEGER NOT NULL")
        TIME: Final = (
            "time",
            "INTEGER NOT NULL")

        AMOUNT: Final = (
            "amount",
            "INTEGER NOT NULL")
        FEE_AMOUNT: Final = (
            "fee_amount",
            "INTEGER NOT NULL")

        IS_COINBASE: Final = (
            "is_coinbase",
            "INTEGER NOT NULL")

    @classproperty
    def _CONSTRAINT_LIST(cls) -> Tuple[str, ...]:  # noqa
        from .coin import CoinListTable
        return (
            f"FOREIGN KEY ("
            f"{cls.ColumnEnum.COIN_ROW_ID})"
            f" REFERENCES {CoinListTable} ("
            f"{CoinListTable.ColumnEnum.ROW_ID})"
            f" ON DELETE CASCADE",
        )

    _UNIQUE_COLUMN_LIST = (
        (ColumnEnum.COIN_ROW_ID, ColumnEnum.NAME),
    )

    def _deserializeStatement(
            self,
            column_list: List[Column],
            key_columns: Dict[Column, Any],
            *,
            address_row_id: int = -1,
            **options) -> Tuple[str, List[Any]]:
        from .maps import AddressTxMapTable

        assert address_row_id > 0
        where_expression, where_args = \
            self._database[AddressTxMapTable].statementSelectTransactions(
                address_row_id)
        return (
            (
                f"SELECT {Column.join(column_list)}"
                f" FROM {self}"
                f" WHERE {self.ColumnEnum.ROW_ID} IN ({where_expression})"
            ),
            where_args
        )

    # TODO dynamic interface with coin.txList
    def deserializeAll(
            self,
            cursor: Cursor,
            address: Coin.Address) -> bool:
        from .tx_io import TxIoListTable

        assert address.coin.rowId > 0
        assert address.rowId > 0

        error = False
        for result in self._deserialize(
                cursor,
                address.coin.Tx,
                {
                    self.ColumnEnum.COIN_ROW_ID: address.coin.rowId
                },
                (
                        (self.ColumnEnum.HEIGHT, SortOrder.ASC),
                        (self.ColumnEnum.TIME, SortOrder.ASC)
                ),
                address_row_id=address.rowId
        ):
            input_error, result["input_list"] = \
                self._database[TxIoListTable].deserializeAll(
                    cursor.connection.cursor(),
                    address.coin,
                    result["row_id"],
                    TxIoListTable.IoType.INPUT)
            output_error, result["output_list"] = \
                self._database[TxIoListTable].deserializeAll(
                    cursor.connection.cursor(),
                    address.coin,
                    result["row_id"],
                    TxIoListTable.IoType.OUTPUT)
            if input_error or output_error:
                error = True

            tx = address.coin.Tx.deserialize(result, address.coin)
            if tx is None:
                error = True
                self._database.logDeserializeError(address.coin.Tx, result)
            else:
                assert tx.rowId > 0
                address.appendTx(tx)
        return not error

    def serialize(
            self,
            cursor: Cursor,
            address: Optional[Coin.Address],
            tx: Coin.Tx) -> None:
        from .tx_io import TxIoListTable
        from .maps import AddressTxMapTable

        assert tx.coin.rowId > 0

        self._serialize(
            cursor,
            tx,
            [
                ColumnValue(self.ColumnEnum.COIN_ROW_ID, tx.coin.rowId),
                ColumnValue(self.ColumnEnum.NAME, tx.name)
            ])
        assert tx.rowId > 0

        # TODO delete old list?
        for io_type, io_list in (
                (TxIoListTable.IoType.INPUT, tx.inputList),
                (TxIoListTable.IoType.OUTPUT, tx.outputList)
        ):
            for io in io_list:
                self._database[TxIoListTable].serialize(
                    cursor,
                    tx,
                    io_type,
                    io)

        if address is not None:
            assert tx.coin.rowId == address.coin.rowId
            self._database[AddressTxMapTable].insert(
                cursor,
                address.rowId,
                tx.rowId)
