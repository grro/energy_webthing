from datetime import datetime, timedelta


class Measure:

    def __init__(self, window_sec: int = 5):
        self.__window_sec = window_sec
        self.__value = 0
        self.__last_fetched_value = 0
        self.__last_fetch_date = datetime.now()

    def set_and_get(self, new_value: int):
        self.__value = new_value
        now = datetime.now()
        if self.__last_fetch_date + timedelta(seconds = self.__window_sec) < now:
            self.__last_fetch_date = now
            self.__last_fetched_value = self.__value
        return self.__last_fetched_value
