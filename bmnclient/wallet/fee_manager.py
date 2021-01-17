
import logging

import PySide2.QtCore as qt_core

from .. import meta

log = logging.getLogger(__name__)
# NET timer TO
UPDATE_FEE_TIMEOUT = 30*60*1000
# LOCAL timer TO
UPDATE_FORCE_FEE_TIMEOUT = 10*60*1000


class FeeManager(qt_core.QObject):

    def __init__(self, parent=None, init: dict = None):
        super().__init__(parent=parent)
        self._timer = qt_core.QTime()
        # 18.02.2020
        # {"fastestFee":14,"halfHourFee":14,"hourFee":2}
        if init is None:
            self._time_values = {
                15: 10,
                14: 30,
                2: 60,
            }
        else:
            self._time_values = init

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
        if self.parent():
            if self._timer.isNull() or self._timer.elapsed() > UPDATE_FORCE_FEE_TIMEOUT:
                self._timer.restart()
                self.parent().retrieve_fee()

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
