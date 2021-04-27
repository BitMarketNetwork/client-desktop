# JOK+++
from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from ..wallet.address import CAddress
from ..wallet.key import AddressType

if TYPE_CHECKING:
    from typing import Dict, List
    from .address import AbstractAddress
    from .coin import AbstractCoin


class HdAddressIterator(Iterator):
    _EMPTY_ADDRESS_LIMIT = 6

    def __init__(self, coin: AbstractCoin, hd_index=0) -> None:
        self._coin = coin
        self._empty_address_list: Dict[
            AbstractAddress.Type,
            List[CAddress]] = {}
        self._skip_address_type_list: List[AbstractAddress.Type] = []
        self._type_index = -1
        self._hd_index = hd_index

    def __iter__(self) -> HdAddressIterator:
        return self

    def __next__(self) -> CAddress:
        while True:
            startup_type_index = self._type_index
            for type_index, address_type in enumerate(self._coin.address.Type):
                if (
                        type_index <= self._type_index
                        or address_type.value[1] <= 0
                        or address_type in self._skip_address_type_list
                ):
                    continue

                if address_type.value[2] == "p2pkh":
                    address_type_old = AddressType.P2PKH
                elif address_type.value[2] == "p2wpkh":
                    address_type_old = AddressType.P2WPKH
                else:
                    continue

                self._type_index = type_index
                hd_path = self._coin.hdAddressPath(0, False, self._hd_index)
                address = CAddress(
                    self._coin,
                    name=hd_path.to_address(address_type_old),
                    type_=address_type)
                address.set_prv_key(hd_path)
                return address

            if startup_type_index < 0:
                raise StopIteration
            self._type_index = -1
            self._hd_index += 1

    def _emptyAddressList(
            self,
            address_type: AbstractAddress.Type) -> List[CAddress]:
        return self._empty_address_list.setdefault(address_type, [])

    def flushEmptyAddressList(self, address_type: AbstractAddress.Type) -> None:
        empty_list = self._emptyAddressList(address_type)
        for empty_address in empty_list:
            self._coin.appendAddress(empty_address)
        empty_list.clear()

    def appendEmptyAddress(self, address: CAddress) -> None:
        empty_list = self._emptyAddressList(address.addressType)
        empty_list.append(address)

        if len(empty_list) >= self._EMPTY_ADDRESS_LIMIT:
            if address.addressType not in self._skip_address_type_list:
                self._skip_address_type_list.append(address.addressType)
