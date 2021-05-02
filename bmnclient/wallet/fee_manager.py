from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import PySide2.QtCore as qt_core

if TYPE_CHECKING:
    from . import Application

log = logging.getLogger(__name__)
UPDATE_FEE_TIMEOUT = 30*60*1000
UPDATE_FORCE_FEE_TIMEOUT = 10*60*1000


class FeeManager(qt_core.QObject):
    def __init__(self, application: Application):
        super().__init__()
        self._application = application

        self._timer = qt_core.QTime()
        # 18.02.2020
        # {"fastestFee":14,"halfHourFee":14,"hourFee":2}
        self._time_values = {
            15: 10,
            14: 30,
            2: 60,
        }

    def add_fee(self, spb: int, minutes: int):
        """
        sets new fee value for each interval
        """
        self._time_values[spb] = minutes
        self._timer.restart()

    def add_fees(self, values: dict):
        self._time_values = values
        self._timer.restart()
        log.debug(sorted(self._time_values))

    def _update(self):
        #if self.parent():
        if True:
            if self._timer.isNull() or self._timer.elapsed() > UPDATE_FORCE_FEE_TIMEOUT:
                from ..application import CoreApplication
                self._timer.restart()
                #CoreApplication.instance().networkThread.retrieve_fee()

    def get_minutes(self, spb: int):
        self._update()
        #       return next(minutes for (sb, minutes) in sorted(self._time_values.items()) if spb >= sb)
        prev_key, prev_val = None, None
        sorted_ = sorted(self._time_values.items())

        log.debug(f"spb:{spb} sorted fee table: {sorted_}")
        for key, val in sorted_:
            if spb <= key:
                # log.debug(f"{spb} {key} {val} ==  {prev_key} {prev_val}")
                if prev_key is None or spb == key:
                    return val
                if key - spb < spb - prev_key:
                    return val
                return prev_val
                # no aproximation
                # return max(val + (val - prev_val) / (key - prev_key) * (spb - prev_key), 0)
            prev_key, prev_val = key, val
        return 0

    @property
    def time_table(self):
        return sorted(self._time_values.items(),)

    @property
    def min_spb(self) -> int:
        return sorted(self._time_values.keys())[0]

    @property
    def max_spb(self) -> int:
        return sorted(self._time_values.keys())[-1]
