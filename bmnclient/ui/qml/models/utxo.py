from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractModel
from .abstract import AbstractCoinObjectModel
from ....coins.abstract import Coin

if TYPE_CHECKING:
    from .. import QmlApplication


class UtxoModel(AbstractCoinObjectModel, Coin.Tx.Utxo.Model, AbstractModel):
    def __init__(self, application: QmlApplication, utxo: Coin.Tx.Utxo) -> None:
        super().__init__(application, utxo=utxo)