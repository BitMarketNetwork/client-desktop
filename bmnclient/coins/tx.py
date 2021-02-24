# JOK++
from __future__ import annotations

from typing import List, Optional

from .address import AbstractAddress


class AbstractTxIo(AbstractAddress):
    pass


class TxModelInterface:
    def beforeAppendInput(self, tx_input: AbstractTxIo) -> None:
        raise NotImplementedError

    def afterAppendInput(self, tx_input: AbstractTxIo) -> None:
        raise NotImplementedError

    def beforeAppendOutput(self, tx_output: AbstractTxIo) -> None:
        raise NotImplementedError

    def afterAppendOutput(self, tx_output: AbstractTxIo) -> None:
        raise NotImplementedError


class AbstractTx:
    class _TxIo(AbstractTxIo):
        pass

    def __init__(self, *, address: AbstractAddress) -> None:
        self._address = address
        self._input_list = []
        self._output_list = []

        self._model: Optional[TxModelInterface] = \
            self._address.coin.model_factory(self)

    @property
    def address(self) -> AbstractAddress:
        return self._address

    @property
    def model(self) -> Optional[TxModelInterface]:
        return self._model

    @property
    def inputList(self) -> List[_TxIo]:
        return self._input_list

    @property
    def outputList(self) -> List[_TxIo]:
        return self._output_list

    def appendInput(self, tx_input: _TxIo) -> bool:
        if self._model:
            self._model.beforeAppendInput(tx_input)
        self._input_list.append(tx_input)
        if self._model:
            self._model.afterAppendInput(tx_input)

        return True

    def appendOutput(self, tx_output: _TxIo) -> bool:
        if self._model:
            self._model.beforeAppendOutput(tx_output)
        self._output_list.append(tx_output)
        if self._model:
            self._model.afterAppendOutput(tx_output)

        return True
