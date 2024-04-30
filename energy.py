from requests import Session
import logging
from threading import Thread
from datetime import datetime, timedelta
from time import sleep
from typing import Tuple, List
from redzoo.database.simple import SimpleDB



def query_3em(meter_addr: str, s: Session) -> Tuple[int, int, int, int]:
    uri = meter_addr + '/rpc/EM.GetStatus?id=0'
    data = s.get(uri, timeout=7).json()
    current_power = round(data['total_act_power'])
    current_power_phase_a = round(data['a_act_power'])
    current_power_phase_b = round(data['b_act_power'])
    current_power_phase_c = round(data['c_act_power'])
    return current_power, current_power_phase_a, current_power_phase_b, current_power_phase_c


def query_pro1(meter_addr: str, s: Session) -> int:
    uri = meter_addr + '/rpc/switch.GetStatus?id=0'
    data = s.get(uri, timeout=7).json()
    return round(data['apower'])




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


class AggregatedPower:

    def __init__(self, name: str, directory : str):
        self.__power_per_minute = SimpleDB(name+ "_per_minute", sync_period_sec=60, directory=directory)
        self.__power_per_hour = SimpleDB(name+ "_per_hour", sync_period_sec=70, directory=directory)
        self.__power_per_day = SimpleDB(name + "_per_day", sync_period_sec=80, directory=directory)

    def measure(self, power_1m: int):
        self.__power_per_minute.put(str(datetime.now().minute), power_1m, ttl_sec=61*60)
        # hourly value
        power_60min = int(sum([self.__power_per_minute.get(str(minute), 0) for minute in range(0, 60)]) / 60)
        self.__power_per_hour.put(str(datetime.now().hour), power_60min, ttl_sec=25*60*60)
        # daily value
        power_24hour =  sum([self.__power_per_hour.get(str(hour), 0) for hour in range(0, 24)])
        self.__power_per_day.put(datetime.now().strftime('%j'), power_24hour, ttl_sec=366 * 24 * 60 * 60)

    @property
    def power_current_day(self) -> int:
        return int(self.__power_per_day.get(str(datetime.now().strftime('%j')), 0))

    @property
    def power_current_hour(self) -> int:
        return self.__power_per_hour.get(str(datetime.now().hour), 0)

    @property
    def power_current_year(self) -> int:
        return sum([self.__power_per_day.get(str(day), 0) for day in range(0, int(datetime.now().strftime('%j'))+1)])

    @property
    def power_estimated_year(self) -> int:
        current_day = int(datetime.now().strftime('%j'))
        watt_current_year = sum([self.__power_per_day.get(str(day), 0) for day in range(0, current_day+1)])
        return int(365*watt_current_year/current_day)





class Energy:

    def __init__(self, meter_addr_provider: str, meter_addr_pv: str, directory: str):
        self.__is_running = True
        self.listener = lambda: None    # "empty" listener
        self.__session = Session()
        self.meter_addr_provider = meter_addr_provider
        self.meter_addr_pv = meter_addr_pv

        self.provider_measures_updated = datetime.now()
        self.provider_power = 0
        self.provider_power_phase_a = 0
        self.provider_power_phase_b = 0
        self.provider_power_phase_c = 0
        self.__provider_aggregated_power = AggregatedPower("provider", directory)

        self.pv_measures_updated = datetime.now()
        self.pv_power = 0
        self.__pv_aggregated_power = AggregatedPower("pv", directory)
        self.__pv_effective_aggregated_power = AggregatedPower("pv_effective", directory)
        self.__consumption_aggregated_power = AggregatedPower("consumption", directory)
        self.__surplus_aggregated_power = AggregatedPower("surplus", directory)

        self.__pv_power_smoothen_recorder = WattRecorder()
        self.__pv_effective_power_smoothen_recorder = WattRecorder()
        self.__provider_power_smoothen_recorder = WattRecorder()
        self.__consumption_power_smoothen_recorder = WattRecorder()
        self.__pv_surplus_power_smoothen_recorder = WattRecorder()


    def set_listener(self, listener):
        self.listener = listener

    @property
    def pv_effective_power(self) -> int:
        if self.provider_power >= 0:
            return self.pv_power
        else:
            effective = self.pv_power - abs(self.provider_power)
            if effective > 0:
                return effective
        return 0

    @property
    def pv_surplus_power(self) -> int:
        if self.provider_power > 0:
            return 0
        else:
            return self.provider_power * -1


    @property
    def consumption_power(self) -> int:
        # e.g:
        # provider 450 + pv 0 = 450
        # provider 300 + pv 200 = 500
        # provider -900 + pv 1600 = 500
        return self.provider_power + self.pv_power

    @property
    def consumption_power_1m(self) -> int:
        return self.__consumption_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def consumption_power_3m(self) -> int:
        return self.__consumption_power_smoothen_recorder.watt_per_hour(minute_range=3)

    @property
    def consumption_power_current_hour(self) -> int:
        return self.__consumption_aggregated_power.power_current_hour

    @property
    def consumption_power_current_day(self) -> int:
        return self.__consumption_aggregated_power.power_current_day

    @property
    def consumption_power_current_year(self) -> int:
        return self.__consumption_aggregated_power.power_current_year

    @property
    def consumption_power_estimated_year(self) -> int:
        return self.__consumption_aggregated_power.power_estimated_year

    @property
    def provider_power_1m(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def provider_power_3m(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(minute_range=3)

    @property
    def provider_power_current_hour(self) -> int:
        return self.__provider_aggregated_power.power_current_hour

    @property
    def provider_power_current_day(self) -> int:
        return self.__provider_aggregated_power.power_current_day

    @property
    def provider_power_current_year(self) -> int:
        return self.__provider_aggregated_power.power_current_year

    @property
    def pv_surplus_power_5s(self) -> int:
        return self.__pv_surplus_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def pv_surplus_power_1m(self) -> int:
        return self.__pv_surplus_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def pv_surplus_power_3m(self) -> int:
        return self.__pv_surplus_power_smoothen_recorder.watt_per_hour(minute_range=3)

    @property
    def pv_surplus_power_5m(self) -> int:
        return self.__pv_surplus_power_smoothen_recorder.watt_per_hour(minute_range=5)

    @property
    def pv_surplus_power_current_hour(self) -> int:
        return self.__surplus_aggregated_power.power_current_hour

    @property
    def pv_effective_power_1m(self) -> int:
        return self.__pv_effective_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def pv_power_1m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def pv_power_3m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=3)

    @property
    def pv_power_current_hour(self) -> int:
        return self.__pv_aggregated_power.power_current_hour

    @property
    def pv_power_current_year(self) -> int:
        return self.__pv_aggregated_power.power_current_year

    @property
    def pv_power_estimated_year(self) -> int:
        return self.__pv_aggregated_power.power_estimated_year

    @property
    def pv_effective_power_estimated_year(self) -> int:
        return self.__pv_effective_aggregated_power.power_estimated_year

    def start(self):
        Thread(target=self.__measure, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __measure(self):
        while self.__is_running:
            self.__refresh_provider_values()
            self.__refresh_pv_values()
            self.__provider_power_smoothen_recorder.put(self.provider_power)
            self.__consumption_power_smoothen_recorder.put(self.consumption_power)
            self.__pv_power_smoothen_recorder.put(self.pv_power)
            self.__pv_surplus_power_smoothen_recorder.put(self.pv_surplus_power)
            self.__pv_effective_power_smoothen_recorder.put(self.pv_effective_power)
            self.__measure_daily_values()
            self.listener()
            sleep(1)

    def __measure_daily_values(self):
        self.__provider_aggregated_power.measure(self.provider_power_1m)
        self.__pv_aggregated_power.measure(self.pv_power_1m)
        self.__pv_effective_aggregated_power.measure(self.pv_effective_power_1m)
        self.__consumption_aggregated_power.measure(self.consumption_power_1m)
        self.__surplus_aggregated_power.measure(self.pv_surplus_power_1m)

    @property
    def pv_power_current_day(self) -> int:
        return self.__pv_aggregated_power.power_current_day

    @property
    def consumption_power_day(self) -> int:
        return self.__consumption_aggregated_power.power_current_day

    def __refresh_provider_values(self):
        try:
            self.provider_power, self.provider_power_phase_a, self.provider_power_phase_b, self.provider_power_phase_c = query_3em(self.meter_addr_provider, self.__session)
            self.provider_measures_updated = datetime.now()
        except Exception as e:
            logging.warning(str(e))
            self.__renew_session()

    def __refresh_pv_values(self):
        try:
            pv_power = query_pro1(self.meter_addr_pv, self.__session)
            if pv_power > 0:
                self.pv_power = pv_power
            else:
                self.pv_power = 0
            self.pv_measures_updated = datetime.now()
        except Exception as e:
            logging.warning(str(e))
            self.__renew_session()

    def __renew_session(self):
        logging.info("renew session")
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()
