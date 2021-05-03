# TODO
# spb == satoshis per byte
class FeeManager:
    def __init__(self) -> None:
        # TODO

        # 03.05.2021
        # https://bitcoinfees.earn.com/api/v1/fees/recommended
        # {"fastestFee":102,"halfHourFee":102,"hourFee":88}
        self._time_values = {
            103: 10,
            102: 30,
            88: 60,
        }

    def get_minutes(self, spb: int) -> int:
        prev_key, prev_val = None, None
        for key, val in sorted(self._time_values.items()):
            if spb <= key:
                if prev_key is None or spb == key:
                    return val
                if key - spb < spb - prev_key:
                    return val
                return prev_val
            prev_key, prev_val = key, val
        return 0

    @property
    def min_spb(self) -> int:
        return sorted(self._time_values.keys())[0]

    @property
    def max_spb(self) -> int:
        return sorted(self._time_values.keys())[-1]
