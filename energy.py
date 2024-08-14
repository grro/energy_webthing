from requests import Session
import logging
from threading import Thread
from datetime import datetime, timedelta
from time import sleep
from typing import Tuple, List, Dict, Optional
from redzoo.database.simple import SimpleDB




class Shelly3em:

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> Tuple[int, int, int, int]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/EM.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    current_power = round(data['total_act_power'])
                    current_power_phase_a = round(data['a_act_power'])
                    current_power_phase_b = round(data['b_act_power'])
                    current_power_phase_c = round(data['c_act_power'])
                    return current_power, current_power_phase_a, current_power_phase_b, current_power_phase_c
                except Exception as e:
                    ex = Exception("Shelly3em called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("Shelly3em called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex

    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()


class Shelly1pro:

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> int:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/switch.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return round(data['apower'])
                except Exception as e:
                    ex = Exception("Shelly1pro called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("Shelly1pro called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex


    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()


class Shelly1pm:

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> int:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/status'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return round(data['meters'][0]['power'])
                except Exception as e:
                    ex = Exception("Shelly1pm called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("Shelly1pm called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex


    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()


class ShellyPmMini:

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> Tuple[int, int, int, int]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetStatus?channel=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    current_power = round(data['pm1:0']['apower'])
                    return current_power
                except Exception as e:
                    ex =  Exception("ShellyPmMini called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("ShellyPmMini called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex

    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()



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


class AggregatedPower:

    def __init__(self, name: str, directory : str):
        self.__power_per_minute = SimpleDB(name+ "_per_minute", sync_period_sec=60, directory=directory)
        self.__power_per_hour = SimpleDB(name+ "_per_hour", sync_period_sec=70, directory=directory)
        self.__power_per_day = SimpleDB(name + "_per_day", sync_period_sec=80, directory=directory)

    def measure(self, power_1m: int):
        self.__power_per_minute.put(str(datetime.utcnow().minute), power_1m, ttl_sec=61*60)
        # hourly value
        power_60min = int(sum([self.__power_per_minute.get(str(minute), 0) for minute in range(0, 60)]) / 60)
        self.__power_per_hour.put(str(datetime.utcnow().hour), power_60min, ttl_sec=25*60*60)
        # daily value
        current_hour = datetime.now().hour
        power_24hour =  sum([self.__power_per_hour.get(str(hour), 0) for hour in range(0, current_hour)])
        self.__power_per_day.put(datetime.utcnow().strftime('%j'), power_24hour, ttl_sec=366 * 24 * 60 * 60)

    @property
    def power_current_day(self) -> int:
        return int(self.__power_per_day.get(str(datetime.utcnow().strftime('%j')), 0))

    @property
    def power_current_hour(self) -> int:
        return self.power_by_hour(datetime.utcnow().hour)

    def power_by_hour(self, hour: int) -> int:
        return self.__power_per_hour.get(str(hour), 0)

    @property
    def power_current_year(self) -> int:
        return sum([self.__power_per_day.get(str(day), 0) for day in range(0, int(datetime.utcnow().strftime('%j'))+1)])

    @property
    def power_estimated_year(self) -> int:
        current_day = int(datetime.utcnow().strftime('%j'))
        power_per_day = [self.__power_per_day.get(str(day), -1) for day in range(0, current_day+1)]
        power_per_day = [power for power in power_per_day if power >= 0]
        if len(power_per_day) > 0:
            return int(sum(power_per_day) * 365 / len(power_per_day))
        else:
            return 0


class Energy:

    def __init__(self,
                 meter_addr_provider: str,
                 meter_addr_pv: str,
                 meter_addr_pv_channel1: str,
                 meter_addr_pv_channel2: str,
                 meter_addr_pv_channel3: str,
                 directory: str,
                 min_pv_power : int):
        self.__is_running = True
        self.__listener = lambda: None    # "empty" listener
        self.__provider_shelly = Shelly3em(meter_addr_provider)
        self.__pv_shelly = Shelly1pro(meter_addr_pv)
        self.__pv_shelly_channel1 = Shelly1pm(meter_addr_pv_channel1)
        self.__pv_shelly_channel2 = ShellyPmMini(meter_addr_pv_channel2)
        self.__pv_shelly_channel3 = ShellyPmMini(meter_addr_pv_channel3)

        self.provider_measures_updated_utc = datetime.utcnow()
        self.provider_power = 0
        self.provider_power_phase_a = 0
        self.provider_power_phase_b = 0
        self.provider_power_phase_c = 0
        self.__provider_aggregated_power = AggregatedPower("provider", directory)

        self.pv_measures_updated = datetime.utcnow()
        self.pv_power = 0
        self.pv_power_channel_1 = 0
        self.pv_power_channel_2 = 0
        self.pv_power_channel_3 = 0
        self.__pv_aggregated_power = AggregatedPower("pv", directory)
        self.__pv_effective_aggregated_power = AggregatedPower("pv_effective", directory)
        self.__consumption_aggregated_power = AggregatedPower("consumption", directory)
        self.__surplus_aggregated_power = AggregatedPower("surplus", directory)

        self.__pv_power_smoothen_recorder = WattRecorder()
        self.__pv_power_ch_1_smoothen_recorder = WattRecorder()
        self.__pv_power_ch_2_smoothen_recorder = WattRecorder()
        self.__pv_power_ch_3_smoothen_recorder = WattRecorder()
        self.__pv_effective_power_smoothen_recorder = WattRecorder()
        self.__provider_power_smoothen_recorder = WattRecorder()
        self.__consumption_power_smoothen_recorder = WattRecorder()
        self.__pv_surplus_power_smoothen_recorder = WattRecorder()

        self.__time_daily_value_measured = datetime.utcnow()

        self.__pv_daily_peeks = SimpleDB("pv_daily_peek", sync_period_sec=60, directory=directory)
        self.__min_pv_power = min_pv_power


    def set_listener(self,listener):
        self.__listener = listener

    @property
    def pv_effective_power(self) -> int:
        effective = self.pv_power - self.pv_surplus_power
        if effective < 0:
            return 0
        else:
            return  effective

    @property
    def pv_surplus_power(self) -> int:
        surplus = 0
        if self.provider_power < 0:
            surplus = abs(self.provider_power)
        if surplus < 0:
            return 0
        else:
            return surplus

    @property
    def consumption_power(self) -> int:
        # e.g:
        # provider 450 + pv 0 = 450
        # provider 300 + pv 200 = 500
        # provider -900 + pv 1600 = 500
        return self.provider_power + self.pv_power

    @property
    def consumption_power_5s(self) -> int:
        return self.__consumption_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def consumption_power_15s(self) -> int:
        return self.__consumption_power_smoothen_recorder.watt_per_hour(second_range=15)

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
    def provider_power_5s(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def provider_power_5s_effective(self) -> int:
        power = self.provider_power_5s
        return 0 if power < 0 else power

    @property
    def provider_power_15s(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def provider_power_15s_effective(self) -> int:
        power = self.provider_power_15s
        return 0 if power < 0 else power

    @property
    def provider_power_1m(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(minute_range=1)

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
    def provider_power_estimated_year(self) -> int:
        return self.__provider_aggregated_power.power_estimated_year

    @property
    def pv_surplus_power_5s(self) -> int:
        return self.__pv_surplus_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def pv_surplus_power_15s(self) -> int:
        return self.__pv_surplus_power_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def pv_surplus_power_1m(self) -> int:
        return self.__pv_surplus_power_smoothen_recorder.watt_per_hour(minute_range=1)

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
    def pv_power_ch1_5s(self) -> int:
        return self.__pv_power_ch_1_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def pv_power_ch1_15s(self) -> int:
        return self.__pv_power_ch_1_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def pv_power_ch2_5s(self) -> int:
        return self.__pv_power_ch_2_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def pv_power_ch2_15s(self) -> int:
        return self.__pv_power_ch_2_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def pv_power_ch3_5s(self) -> int:
        return self.__pv_power_ch_3_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def pv_power_ch3_15s(self) -> int:
        return self.__pv_power_ch_3_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def pv_power_5s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def pv_power_15s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=15)

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

    @property
    def pv_effective_power_current_day(self) -> int:
        return self.__pv_effective_aggregated_power.power_current_day

    @property
    def pv_power_current_day(self) -> int:
        return self.__pv_aggregated_power.power_current_day

    @property
    def pv_peek_hour_utc(self) -> int:
        peeks = sorted(self.__peeks())
        if len(peeks) == 0:
            return 12
        else:
            return peeks[int(len(peeks)* 0.5)]

    def __peeks(self) -> List[int]:
        today = datetime.utcnow()
        hours = [self.__pv_daily_peeks.get((today - timedelta(days=day_offset)).strftime("%Y-%m-%d"), -1) for day_offset in range(0, 60)]
        return [hour for hour in hours if hour >= 0]

    def __peek_info_loop(self):
        while self.__is_running:
            try:
                logging.info("peek: " + str(self.pv_peek_hour_utc) + " utc (peeks: " + ", ".join(str(hour) for hour in self.__peeks()) +")")
            except Exception as e:
                logging.warning("error occurred on printing peek values " + str(e))
            sleep(13 * 60 * 60)

    def __print_percent(self, share: int, total: int) -> str:
        if share == 0 or total == 0:
            return "0%"
        else:
            return str(round(share*100/total, 0)) + "%"

    def __statistics_loop(self):
        reported_date = datetime.now() - timedelta(days=1)
        while self.__is_running:
            try:
                now = datetime.now()
                if now > (reported_date + timedelta(hours=3)):
                    reported_date = now
                    logging.info("power consumption current day:      " + str(round(self.consumption_power_current_day/1000,1)) + " kWh")
                    logging.info("pv power current day:               " + str(round(self.pv_power_current_day/1000,1)) + " kWh")
                    logging.info("pv effective power current day:     " + str(round(self.pv_effective_power_current_day/1000,1)) + " kWh (" + self.__print_percent(self.pv_effective_power_current_day, self.pv_power_current_day) + " efficiency)")
                    logging.info("pv effective power estimated year:  " + str(round(self.pv_effective_power_estimated_year/1000)) + " kWh  (" + self.__print_percent(self.pv_effective_power_estimated_year, self.pv_power_estimated_year) + " efficiency; " + self.__print_percent(self.pv_effective_power_estimated_year, self.pv_effective_power_estimated_year + self.provider_power_estimated_year) + " of total consumption)")
                    logging.info("provider power estimated year:      " + str(round(self.provider_power_estimated_year/1000)) + " kWh  (" + self.__print_percent(self.provider_power_estimated_year, self.pv_effective_power_estimated_year + self.provider_power_estimated_year) + " of total consumption)")
            except Exception as e:
                logging.warning("error occurred on statistics " + str(e))
            sleep(10 * 60)

    @property
    def consumption_power_day(self) -> int:
        return self.__consumption_aggregated_power.power_current_day

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()
        Thread(target=self.__measure_channel1_loop, daemon=True).start()
        Thread(target=self.__measure_channel2_loop, daemon=True).start()
        Thread(target=self.__measure_channel3_loop, daemon=True).start()
        Thread(target=self.__peek_info_loop, daemon=True).start()
        Thread(target=self.__statistics_loop, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __measure_loop(self):
        while self.__is_running:
            try:
                self.__refresh_provider_values()
                self.__refresh_pv_values()
                self.__provider_power_smoothen_recorder.put(self.provider_power)
                self.__consumption_power_smoothen_recorder.put(self.consumption_power)
                self.__pv_power_smoothen_recorder.put(self.pv_power)
                self.__pv_power_ch_1_smoothen_recorder.put(self.pv_power_channel_1)
                self.__pv_power_ch_2_smoothen_recorder.put(self.pv_power_channel_2)
                self.__pv_power_ch_3_smoothen_recorder.put(self.pv_power_channel_3)
                self.__pv_surplus_power_smoothen_recorder.put(self.pv_surplus_power)
                self.__pv_effective_power_smoothen_recorder.put(self.pv_effective_power)
                self.__measure_daily_values()
                self.__listener()
                sleep(1.03)
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
                sleep(3)

    def __measure_channel1_loop(self):
        while self.__is_running:
            try:
                self.__refresh_pv_channel1_values()
                self.__listener()
                sleep(2.03)
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
                sleep(3)

    def __measure_channel2_loop(self):
        while self.__is_running:
            try:
                self.__refresh_pv_channel2_values()
                self.__listener()
                sleep(2.03)
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
                sleep(3)

    def __measure_channel3_loop(self):
        while self.__is_running:
            try:
                self.__refresh_pv_channel3_values()
                self.__listener()
                sleep(2.03)
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
                sleep(3)

    def __refresh_provider_values(self) -> bool:
        try:
            self.provider_power, self.provider_power_phase_a, self.provider_power_phase_b, self.provider_power_phase_c = self.__provider_shelly.query()
            self.provider_measures_updated_utc = datetime.utcnow()
            return True
        except Exception as e:
            return False

    def __refresh_pv_values(self) -> bool:
        try:
            pv_power = self.__pv_shelly.query()
            if pv_power > 0:
                self.pv_power = pv_power
            else:
                self.pv_power = 0
            self.pv_measures_updated = datetime.utcnow()
            return True
        except Exception as e:
            logging.warning("error occurred reading pv values " + str(e))
            return False

    def __refresh_pv_channel1_values(self) -> bool:
        try:
            pv_power_channel_1 = self.__pv_shelly_channel1.query()
            if pv_power_channel_1 > 0:
                self.pv_power_channel_1 = pv_power_channel_1
            else:
                self.pv_power_channel_1 = 0
            return True
        except Exception as e:
            logging.warning("error occurred reading pv values " + str(e))
            return False

    def __refresh_pv_channel2_values(self) -> bool:
        try:
            pv_power_channel_2 = self.__pv_shelly_channel2.query()
            if pv_power_channel_2 > 0:
                self.pv_power_channel_2 = pv_power_channel_2
            else:
                self.pv_power_channel_2 = 0
            return True
        except Exception as e:
            logging.warning("error occurred reading pv values " + str(e))
            return False

    def __refresh_pv_channel3_values(self) -> bool:
        try:
            pv_power_channel_3 = self.__pv_shelly_channel3.query()
            if pv_power_channel_3 > 0:
                self.pv_power_channel_3 = pv_power_channel_3
            else:
                self.pv_power_channel_3 = 0
            return True
        except Exception as e:
            logging.warning("error occurred reading pv values " + str(e))
            return False

    def __measure_daily_values(self):
        if datetime.utcnow() > self.__time_daily_value_measured + timedelta(seconds=29):
            provider = self.provider_power_1m
            if provider < 0:
                provider = 0
            self.__provider_aggregated_power.measure(provider)
            self.__pv_aggregated_power.measure(self.pv_power_1m)
            self.__pv_effective_aggregated_power.measure(self.pv_effective_power_1m)
            self.__consumption_aggregated_power.measure(self.consumption_power_1m)
            self.__surplus_aggregated_power.measure(self.pv_surplus_power_1m)
            self.__time_daily_value_measured = datetime.utcnow()
            self.__compute_daily_pv_peek()

    def __compute_daily_pv_peek(self):
        pv_power_per_hour = { hour: self.__pv_aggregated_power.power_by_hour(hour) for hour in range(0, datetime.utcnow().hour) }
        pv_power_per_hour = { hour: pv_power_per_hour[hour] for hour in pv_power_per_hour.keys() if pv_power_per_hour[hour] > self.__min_pv_power}
        pv_peek_hour = self.__pv_peek_hour_of_day(pv_power_per_hour)
        if pv_peek_hour is not None:
            self.__pv_daily_peeks.put(datetime.utcnow().strftime("%Y-%m-%d"), pv_peek_hour, ttl_sec=30*24*60*60)

    def __pv_peek_hour_of_day(self, pv_power_per_hour: Dict[int, int]) -> Optional[int]:
        aggregated_power_of_day =  sum(pv_power_per_hour.values())
        aggregated = 0
        if len(pv_power_per_hour) > 2:
            for hour, power in pv_power_per_hour.items():
                aggregated += power
                if aggregated > round(aggregated_power_of_day/2):
                    return hour
        return None




