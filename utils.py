from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional


class BufferedValue:

    def __init__(self, window_sec: int = 5, threshold: int = 50):
        self.__window_sec = window_sec
        self._threshold = threshold
        self.__value = 0
        self.__buffered_value = 0
        self.__buffer_date = datetime.now()

    def set_and_get(self, new_value: int):
        self.__value = new_value
        now = datetime.now()

        delta = abs(self.__value - self.__buffered_value)
        if delta < self._threshold:
            expired = (self.__buffer_date + timedelta(seconds = self.__window_sec)) < now
        else:
            expired = (self.__buffer_date + timedelta(seconds = int(self.__window_sec/5))) < now

        if expired:
            self.__buffer_date = now
            self.__buffered_value = self.__value

        return self.__buffered_value





class WattRecorder:

    def __init__(self, max_size_minutes: int = 65):
        self.__max_size_minutes = max_size_minutes
        self.__minute_measures: List[Tuple[datetime, float]] = list()
        self.__value = 0

    @property
    def size(self) -> int:
        return len(self.__minute_measures)

    def put(self, measure: float):
        if len(self.__minute_measures) == 0 or measure != self.__minute_measures[-1][1]:
            self.__minute_measures.append((datetime.utcnow(), measure))
            self.__compact()

    def __compact(self):
        max_datetime = datetime.utcnow() - timedelta(minutes=self.__max_size_minutes)
        num_elements = len(self.__minute_measures)
        for i in range(num_elements):
            if self.__minute_measures[0][0] < max_datetime:
                del self.__minute_measures[0]
            else:
                return

    def watt_per_hour(self, minute_range: int = None, second_range: int = 60) -> int:
        now = datetime.utcnow()
        if minute_range is not None:
            second_range = minute_range * 60
        offset = now - timedelta(seconds=second_range)

        watt_sec = 0
        for measure in reversed(self.__minute_measures):
            start_time = measure[0]
            watt = measure[1]
            if start_time < offset:
                start_time = offset
            elapsed_seconds = (now - start_time).total_seconds()
            watt_sec += watt * elapsed_seconds
            now = start_time
            if start_time == offset:
                break
        return int(watt_sec / second_range)

