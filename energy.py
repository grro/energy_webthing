import random
from random import randint
from requests import request, Session
import logging
from threading import Thread
from datetime import datetime, timedelta
from time import sleep
from typing import Tuple, List


def query_3em(meter_addr: str, s: Session) -> Tuple[int, int, int, int]:
    uri = meter_addr + '/rpc/EM.GetStatus?id=0'
    data = s.get(uri, timeout=10).json()
    current_power = round(data['total_act_power'])
    current_power_phase_a = round(data['a_act_power'])
    current_power_phase_b = round(data['b_act_power'])
    current_power_phase_c = round(data['c_act_power'])
    return current_power, current_power_phase_a, current_power_phase_b, current_power_phase_c


def query_pro1(meter_addr: str, s: Session) -> int:
    uri = meter_addr + '/rpc/switch.GetStatus?id=0'
    data = s.get(uri, timeout=10).json()
    return round(data['apower'])




class WattRecorder:

    def __init__(self, max_size_minutes: int = 20):
        self.__max_size_minutes = max_size_minutes
        self.__minute_measures: List[Tuple[datetime, float]] = list()
        self.__value = 0

    @property
    def size(self) -> int:
        return len(self.__minute_measures)

    def put(self, measure: float):
        if len(self.__minute_measures) == 0 or measure != self.__minute_measures[-1][1]:
            self.__minute_measures.append((datetime.now(), measure))
            self.__compact()

    def __compact(self):
        if len(self.__minute_measures) > 2:
            if datetime.now() > self.__minute_measures[1][0] + timedelta(minutes=self.__max_size_minutes):
                del self.__minute_measures[0]
                self.__compact()

    def watt_per_hour(self, minute_range: int = None, second_range: int = 60) -> int:
        now = datetime.now()
        if minute_range is not None:
            second_range = minute_range * 60
        offset = now - timedelta(seconds=second_range)

        power_per_sec = 0
        for measure in reversed(self.__minute_measures):
            start_time = measure[0]
            if start_time < offset:
                start_time = offset
            timerange = (now - start_time).total_seconds()
            power_per_sec += measure[1] * timerange
            now = measure[0]
            if start_time == offset:
                return int(power_per_sec / second_range)

        return 0



class Energy:

    def __init__(self, meter_addr_provider: str, meter_addr_pv: str):
        self.__is_running = True
        self.listener = lambda: None    # "empty" listener
        self.__session = Session()
        self.meter_addr_provider = meter_addr_provider
        self.meter_addr_pv = meter_addr_pv
        self.current_power_provider = 0
        self.current_power_phase_a_provider = 0
        self.current_power_phase_b_provider = 0
        self.current_power_phase_c_provider = 0
        self.current_power_pv = 0
        self.__current_power_pv_smoothen_recorder = WattRecorder()
        self.__current_power_provider_smoothen_recorder = WattRecorder()
        self.__current_power_consumption_smoothen_recorder = WattRecorder()
        self.__current_power_pv_surplus_smoothen_recorder = WattRecorder()

    def set_listener(self, listener):
        self.listener = listener

    @property
    def current_power_consumption(self) -> int:
        # e.g:
        # provider 450 + pv 0 = 450
        # provider 300 + pv 200 = 500
        # provider -900 + pv 1600 = 500
        return self.current_power_provider + self.current_power_pv

    @property
    def current_power_pv_surplus(self) -> int:
        if self.current_power_provider > 0:
            return 0
        else:
            return self.current_power_provider * -1

    @property
    def current_power_pv_surplus_smoothen_5s(self) -> int:
        return self.__current_power_pv_surplus_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def current_power_pv_surplus_smoothen_1m(self) -> int:
        return self.__current_power_pv_surplus_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def current_power_pv_surplus_smoothen_3m(self) -> int:
        return self.__current_power_pv_surplus_smoothen_recorder.watt_per_hour(minute_range=3)

    @property
    def current_power_pv_surplus_smoothen_5m(self) -> int:
        return self.__current_power_pv_surplus_smoothen_recorder.watt_per_hour(minute_range=5)

    @property
    def current_power_pv_smoothen_1m(self) -> int:
        return self.__current_power_pv_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def current_power_pv_smoothen_3m(self) -> int:
        return self.__current_power_pv_smoothen_recorder.watt_per_hour(minute_range=3)

    @property
    def current_power_consumption_smoothen_1m(self) -> int:
        return self.__current_power_consumption_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def current_power_consumption_smoothen_3m(self) -> int:
        return self.__current_power_consumption_smoothen_recorder.watt_per_hour(minute_range=3)

    def start(self):
        Thread(target=self.__measure, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __measure(self):
        while self.__is_running:
            self.__refresh_provider_values()
            self.__refresh_pv_values()
            self.__current_power_provider_smoothen_recorder.put(self.current_power_provider)
            self.__current_power_pv_smoothen_recorder.put(self.current_power_pv_surplus)
            self.__current_power_consumption_smoothen_recorder.put(self.current_power_consumption)
            self.__current_power_pv_surplus_smoothen_recorder.put(self.current_power_pv_surplus)
            self.listener()
            sleep(1)

    def __refresh_provider_values(self):
        try:
            self.current_power_provider, self.current_power_phase_a_provider, self.current_power_phase_b_provider, self.current_power_phase_c_provider = query_3em(self.meter_addr_provider, self.__session)
        except Exception as e:
            logging.warning(str(e))
            try:
                self.__session.close()
            except Exception as e2:
                logging.warning(str(e2))
            self.__session = Session()

    def __refresh_pv_values(self):
        try:
            self.current_power_pv = query_pro1(self.meter_addr_pv, self.__session)
        except Exception as e:
            logging.warning(str(e))
            try:
                self.__session.close()
            except Exception as e2:
                logging.warning(str(e2))
            self.__session = Session()

