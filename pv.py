import logging
from threading import Thread
from typing import List
from time import sleep
from datetime import datetime, timedelta, UTC
from shelly import ShellyMeter
from utils import WattRecorder
from redzoo.database.simple import SimpleDB



class Module:

    def __init__(self, addr: str, description: str):
        self.__shelly = ShellyMeter(addr, description)
        self.name = self.__shelly.name
        self.power = 0
        self.__pv_power_smoothen_recorder = WattRecorder()

    @property
    def power_5s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def power_15s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def power_1m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def power_5m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=5)

    def measure(self) -> int:
        try:
            power = self.__shelly.measure().total
            power = 0 if power < 0 else power
            self.power = power
            self.__pv_power_smoothen_recorder.put(power)
            return power
        except Exception as e:
            return 0


class Pv:

    def __init__(self, meter_addr_pv_all: str, meter_addr_pv_channel1: str, meter_addr_pv_channel2: str, meter_addr_pv_channel3: str, meter_addr_pv_channel4: str, directory: str):
        self.__is_running = True
        self.__listeners = set()
        self.__all = Module(meter_addr_pv_all, "PV all")
        self.__module1 = Module(meter_addr_pv_channel1, "PV module1")
        self.__module2 = Module(meter_addr_pv_channel2, "PV module2")
        self.__module3 = Module(meter_addr_pv_channel3,"PV module3")
        self.__module4 = Module(meter_addr_pv_channel4,"PV module4")

        self.latest_measurement_date = datetime.now(UTC)

        self.power_downstream = 0

        self.__pv_power_smoothen_recorder = WattRecorder()
        self.__power_per_hour = {}
        self.__surplus_daily_peeks = SimpleDB("spv_daily_peek", sync_period_sec=60, directory=directory)

        logging.info("peek hours " + ",".join([str(peek) for peek in self.__cleaned_peaks()]) + " -> " + str(self.power_peak_hour_utc) + " UTC")


    def elapsed_since_last_measurement_sec(self):
        return (datetime.now(UTC) - self.latest_measurement_date).total_seconds()

    def addd_listener(self,listener):
        self.__listeners.add(listener)

    @property
    def power_downstream_5s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_15s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_1m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=1) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_5m(self) -> int:
        return  self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_60m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=60) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_module1(self) -> int:
        return self.__module1.power

    @property
    def power_downstream_module1_5s(self) -> int:
        return self.__module1.power_5s

    @property
    def power_downstream_module1_15s(self) -> int:
        return self.__module1.power_15s

    @property
    def power_downstream_module1_1m(self) -> int:
        return self.__module1.power_1m

    @property
    def power_downstream_module1_5m(self) -> int:
        return self.__module1.power_5m

    @property
    def power_downstream_module2(self) -> int:
        return self.__module2.power

    @property
    def power_downstream_module2_5s(self) -> int:
        return self.__module2.power_5s

    @property
    def power_downstream_module2_15s(self) -> int:
        return self.__module2.power_15s

    @property
    def power_downstream_module2_1m(self) -> int:
        return self.__module2.power_1m

    @property
    def power_downstream_module2_5m(self) -> int:
        return self.__module2.power_5m

    @property
    def power_downstream_module3(self) -> int:
        return self.__module3.power

    @property
    def power_downstream_module3_5s(self) -> int:
        return self.__module3.power_5s

    @property
    def power_downstream_module3_15s(self) -> int:
        return self.__module3.power_15s

    @property
    def power_downstream_module3_1m(self) -> int:
        return self.__module3.power_1m

    @property
    def power_downstream_module3_5m(self) -> int:
        return self.__module3.power_5m

    @property
    def power_downstream_module4(self) -> int:
        return self.__module4.power

    @property
    def power_downstream_module4_5s(self) -> int:
        return self.__module4.power_5s

    @property
    def power_downstream_module4_15s(self) -> int:
        return self.__module4.power_15s

    @property
    def power_downstream_module4_1m(self) -> int:
        return self.__module4.power_1m

    @property
    def power_downstream_module4_5m(self) -> int:
        return self.__module4.power_5m

    @property
    def power_downstream_module5(self) -> int:
        power5 = self.power_downstream - (self.power_downstream_module1 + self.power_downstream_module2 + self.power_downstream_module3 + self.power_downstream_module4)
        return 0 if power5 <0 else power5

    @property
    def power_downstream_module5_5s(self) -> int:
        power5 = self.power_downstream_5s - (self.power_downstream_module1_5s + self.power_downstream_module2_5s + self.power_downstream_module3_5s + self.power_downstream_module4_5s)
        return 0 if power5 <0 else power5

    @property
    def power_downstream_module5_15s(self) -> int:
        power5 = self.power_downstream_15s - (self.power_downstream_module1_15s + self.power_downstream_module2_15s + self.power_downstream_module3_15s + self.power_downstream_module4_15s)
        return 0 if power5 <0 else power5

    @property
    def power_downstream_module5_1m(self) -> int:
        power5 = self.power_downstream_1m - (self.power_downstream_module1_1m + self.power_downstream_module2_1m + self.power_downstream_module3_1m + self.power_downstream_module4_1m)
        return 0 if power5 <0 else power5

    @property
    def power_downstream_module5_5m(self) -> int:
        power5 = self.power_downstream_5m - (self.power_downstream_module1_5m + self.power_downstream_module2_5m + self.power_downstream_module3_5m + self.power_downstream_module4_5m)
        return 0 if power5 <0 else power5

    @property
    def power_peak_hour_utc(self) -> int:
        peeks = sorted(self.__cleaned_peaks())
        if len(peeks) > 10:
            return peeks[int(len(peeks)* 0.5)]
        else:
            return 12

    def latest_peeks_hour_utc(self) -> List[int]:
        return self.__cleaned_peaks()[:8]

    def __cleaned_peaks(self) -> List[int]:
        today = datetime.now(UTC)
        hours = [self.__surplus_daily_peeks.get((today - timedelta(days=day_offset)).strftime("%Y-%m-%d"), -1) for day_offset in range(0, 60)]
        return [hour for hour in hours if 15 > hour > 9]

    def add_listener(self,listener):
        self.__listeners.add(listener)

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()
        Thread(target=self.__day_peek_loop, daemon=True).start()
        Thread(target=self.__peek_loop, daemon=True).start()
        Thread(target=self.__info_loop, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __measure_loop(self):
        while self.__is_running:
            try:
                self.__measure()
                [listener() for listener in self.__listeners]
                self.latest_measurement_date = datetime.now(UTC)
                sleep(1.03)
            except Exception as e:
                logging.warning("error occurred on pv refresh " + str(e))
                sleep(3)

    def __measure(self):
        self.__module1.measure()
        self.__module2.measure()
        self.__module3.measure()
        self.__module4.measure()
        power_all = self.__all.measure()
        self.power_downstream = 0 if power_all <0 else power_all
        self.__pv_power_smoothen_recorder.put(self.power_downstream)

    def __day_peek_loop(self):
        while self.__is_running:
            try:
                self.__power_per_hour[datetime.now().hour] = self.power_downstream_60m
            except Exception as e:
                logging.warning("error occurred on printing peek values " + str(e))
            sleep(1*60)

    def __peek_loop(self):
        while self.__is_running:
            try:
                if datetime.now().hour >= 22:
                    peek_hour = 0
                    peek_value = 0
                    for hour in range(0, 23):
                        peek = self.__power_per_hour.get(hour, 0)
                        if peek > 600:
                            if peek > peek_value:
                                peek_hour = hour
                                peek_value = peek

                    date = datetime.now(UTC).strftime("%Y-%m-%d")
                    if self.__surplus_daily_peeks.get(date, -1) != peek_hour:
                        logging.info("peek on hour " + str(peek_hour) + ", peek " + str(peek_value))
                    self.__surplus_daily_peeks.put(date, peek_hour, ttl_sec=30*24*60*60)   # ttl 30 day
            except Exception as e:
                logging.warning("error occurred on printing peek values " + str(e))
            sleep(17*60)


    def __info_loop(self):
        sleep(1 * 60)
        while self.__is_running:
            try:
                logging.info(self.info())
                sleep(10*60)
            except Exception as e:
                logging.warning("error occurred on info " + str(e))
                sleep(3 * 60)

    def info(self) -> str:
        return "PV " + str(int(self.power_downstream_1m)) + "W" + \
                " (module1: " + str(int(self.power_downstream_module1_1m)) + "W," + \
                " module2: " + str(int(self.power_downstream_module2_1m)) + "W," + \
                " module3: " + str(int(self.power_downstream_module3_1m)) + "W," + \
                " module4: " + str(int(self.power_downstream_module4_1m)) + "W" + \
                " module5: " + str(int(self.power_downstream_module5_1m)) + "W" + \
                ", peek hour: " + str(self.power_peak_hour_utc) + ")"



