import tornado.ioloop
import logging
from threading import Thread
from typing import List
from time import sleep
from datetime import datetime, timedelta, UTC
from webthing import (Property, Thing, Value)
from shelly import ShellyMeter
from utils import WattRecorder, BufferedValue
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
        self.__power_downstream_5s = BufferedValue()
        self.__power_downstream_1m = BufferedValue()

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
        return self.__power_downstream_5s.set_and_get(self.__pv_power_smoothen_recorder.watt_per_hour(second_range=5)) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_15s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_1m(self) -> int:
        return self.__power_downstream_1m.set_and_get(self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=1)) if self.elapsed_since_last_measurement_sec() < 60 else 0

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
        power4 = self.power_downstream - (self.power_downstream_module1 + self.power_downstream_module2 + self.power_downstream_module3 + self.power_downstream_module4)
        return 0 if power4 <0 else power4

    @property
    def power_downstream_module5_5s(self) -> int:
        power4 = self.power_downstream_5s - (self.power_downstream_module1_5s + self.power_downstream_module2_5s + self.power_downstream_module3_5s + self.power_downstream_module4_5s)
        return 0 if power4 <0 else power4

    @property
    def power_downstream_module5_15s(self) -> int:
        power4 = self.power_downstream_15s - (self.power_downstream_module1_15s + self.power_downstream_module2_15s + self.power_downstream_module3_15s + self.power_downstream_module4_15s)
        return 0 if power4 <0 else power4

    @property
    def power_downstream_module5_1m(self) -> int:
        power4 = self.power_downstream_1m - (self.power_downstream_module1_1m + self.power_downstream_module2_1m + self.power_downstream_module3_1m + self.power_downstream_module4_1m)
        return 0 if power4 <0 else power4

    @property
    def power_downstream_module5_5m(self) -> int:
        power4 = self.power_downstream_5m - (self.power_downstream_module1_5m + self.power_downstream_module2_5m + self.power_downstream_module3_5m + self.power_downstream_module4_5m)
        return 0 if power4 <0 else power4


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





class PvThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, pv: Pv):
        Thing.__init__(
            self,
            'urn:dev:ops:pv',
            'PvSensor',
            ['MultiLevelSensor'],
            "pv"
        )
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.pv = pv
        self.pv.add_listener(self.on_value_changed)


        self.power_downstream = Value(pv.power_downstream)
        self.add_property(
            Property(self,
                     'power_downstream',
                     self.power_downstream,
                     metadata={
                         'title': 'power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the pv',
                         'readOnly': True,
                     }))

        self.power_downstream_5s = Value(pv.power_downstream_5s)
        self.add_property(
            Property(self,
                     'power_downstream_5s',
                     self.power_downstream_5s,
                     metadata={
                         'title': 'power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the pv  (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_15s = Value(pv.power_downstream_15s)
        self.add_property(
            Property(self,
                     'power_downstream_15s',
                     self.power_downstream_15s,
                     metadata={
                         'title': 'power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the pv  (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_1m = Value(pv.power_downstream_1m)
        self.add_property(
            Property(self,
                     'power_downstream_1m',
                     self.power_downstream_1m,
                     metadata={
                         'title': 'power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the pv  (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_5m = Value(pv.power_downstream_5m)
        self.add_property(
            Property(self,
                     'power_downstream_5m',
                     self.power_downstream_5m,
                     metadata={
                         'title': 'power downstream 5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the pv  (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1 = Value(pv.power_downstream_module1)
        self.add_property(
            Property(self,
                     'module1_power_downstream',
                     self.power_downstream_module1,
                     metadata={
                         'title': 'module1 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module1',
                         'readOnly': True,
                     }))

        self.power_downstream_module1_5s = Value(pv.power_downstream_module1_5s)
        self.add_property(
            Property(self,
                     'module1_power_downstream_5s',
                     self.power_downstream_module1_5s,
                     metadata={
                         'title': 'module1 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 1 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1_15s = Value(pv.power_downstream_module1_15s)
        self.add_property(
            Property(self,
                     'module1_power_downstream_15s',
                     self.power_downstream_module1_15s,
                     metadata={
                         'title': 'module1 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 1 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1_1m = Value(pv.power_downstream_module1_1m)
        self.add_property(
            Property(self,
                     'module1_power_downstream_1m',
                     self.power_downstream_module1_1m,
                     metadata={
                         'title': 'module1 power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 1 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1_5m = Value(pv.power_downstream_module1_5m)
        self.add_property(
            Property(self,
                     'module1_power_downstream_5m',
                     self.power_downstream_module1_5m,
                     metadata={
                         'title': 'module1 power downstream 5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 1 (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module2 = Value(pv.power_downstream_module2)
        self.add_property(
            Property(self,
                     'module2_power_downstream',
                     self.power_downstream_module2,
                     metadata={
                         'title': 'module2 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module2',
                         'readOnly': True,
                     }))

        self.power_downstream_module2_5s = Value(pv.power_downstream_module2_5s)
        self.add_property(
            Property(self,
                     'module2_power_downstream_5s',
                     self.power_downstream_module2_5s,
                     metadata={
                         'title': 'module1 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 2 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module2_15s = Value(pv.power_downstream_module2_15s)
        self.add_property(
            Property(self,
                     'module2_power_downstream_15s',
                     self.power_downstream_module2_15s,
                     metadata={
                         'title': 'module2 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 2 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module2_1m = Value(pv.power_downstream_module2_1m)
        self.add_property(
            Property(self,
                     'module2_power_downstream_1m',
                     self.power_downstream_module2_1m,
                     metadata={
                         'title': 'module2 power downstream 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 2 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module2_5m = Value(pv.power_downstream_module2_5m)
        self.add_property(
            Property(self,
                     'module2_power_downstream_5m',
                     self.power_downstream_module2_5m,
                     metadata={
                         'title': 'module2 power downstream 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 2 (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module3 = Value(pv.power_downstream_module3)
        self.add_property(
            Property(self,
                     'module3_power_downstream',
                     self.power_downstream_module3,
                     metadata={
                         'title': 'module3 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module3',
                         'readOnly': True,
                     }))

        self.power_downstream_module3_5s = Value(pv.power_downstream_module3_5s)
        self.add_property(
            Property(self,
                     'module3_power_downstream_5s',
                     self.power_downstream_module3_5s,
                     metadata={
                         'title': 'module3 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 3 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module3_15s = Value(pv.power_downstream_module3_15s)
        self.add_property(
            Property(self,
                     'module3_power_downstream_15s',
                     self.power_downstream_module3_15s,
                     metadata={
                         'title': 'module3 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 3 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module3_1m = Value(pv.power_downstream_module3_1m)
        self.add_property(
            Property(self,
                     'module3_power_downstream_1m',
                     self.power_downstream_module3_1m,
                     metadata={
                         'title': 'module3 power downstream 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 3 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module3_5m = Value(pv.power_downstream_module3_5m)
        self.add_property(
            Property(self,
                     'module3_power_downstream_5m',
                     self.power_downstream_module3_5m,
                     metadata={
                         'title': 'module3 power downstream 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 3 (smoothen 5 min)',
                         'readOnly': True,
                     }))


        self.power_downstream_module4 = Value(pv.power_downstream_module4)
        self.add_property(
            Property(self,
                     'module4_power_downstream',
                     self.power_downstream_module4,
                     metadata={
                         'title': 'module4 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module4',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_5s = Value(pv.power_downstream_module4_5s)
        self.add_property(
            Property(self,
                     'module4_power_downstream_5s',
                     self.power_downstream_module4_5s,
                     metadata={
                         'title': 'module4 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_15s = Value(pv.power_downstream_module4_15s)
        self.add_property(
            Property(self,
                     'module4_power_downstream_15s',
                     self.power_downstream_module4_15s,
                     metadata={
                         'title': 'module4 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_15s = Value(pv.power_downstream_module4_15s)
        self.add_property(
            Property(self,
                     'module4_power_downstream_15s',
                     self.power_downstream_module4_15s,
                     metadata={
                         'title': 'module4 power downstream 15 sec',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_1m = Value(pv.power_downstream_module4_1m)
        self.add_property(
            Property(self,
                     'module4_power_downstream_1m',
                     self.power_downstream_module4_1m,
                     metadata={
                         'title': 'module4 power downstream 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_5m = Value(pv.power_downstream_module4_5m)
        self.add_property(
            Property(self,
                     'module4_power_downstream_5m',
                     self.power_downstream_module4_5m,
                     metadata={
                         'title': 'module4 power downstream 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 5 min)',
                         'readOnly': True,
                     }))


        self.power_downstream_module5 = Value(pv.power_downstream_module5)
        self.add_property(
            Property(self,
                     'module5_power_downstream',
                     self.power_downstream_module5,
                     metadata={
                         'title': 'module5 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module 5',
                         'readOnly': True,
                     }))

        self.power_downstream_module5_5s = Value(pv.power_downstream_module5_5s)
        self.add_property(
            Property(self,
                     'module5_power_downstream_5s',
                     self.power_downstream_module5_5s,
                     metadata={
                         'title': 'module5 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 5 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module5_15s = Value(pv.power_downstream_module5_15s)
        self.add_property(
            Property(self,
                     'module5_power_downstream_15s',
                     self.power_downstream_module5_15s,
                     metadata={
                         'title': 'module5 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 5 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module5_15s = Value(pv.power_downstream_module5_15s)
        self.add_property(
            Property(self,
                     'module5_power_downstream_15s',
                     self.power_downstream_module5_15s,
                     metadata={
                         'title': 'module5 power downstream 15 sec',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 5 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module5_1m = Value(pv.power_downstream_module5_1m)
        self.add_property(
            Property(self,
                     'module5_power_downstream_1m',
                     self.power_downstream_module5_1m,
                     metadata={
                         'title': 'module5 power downstream 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 5 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module5_5m = Value(pv.power_downstream_module5_5m)
        self.add_property(
            Property(self,
                     'module5_power_downstream_5m',
                     self.power_downstream_module5_5m,
                     metadata={
                         'title': 'module5 power downstream 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 5 (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1u2_5m = Value(pv.power_downstream_module1_5m + pv.power_downstream_module2_5m)
        self.add_property(
            Property(self,
                     'module1u2_power_downstream_5m',
                     self.power_downstream_module1u2_5m,
                     metadata={
                         'title': 'module1 + module2 power downstream 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module1 + module2 (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1u2u3_5m = Value(pv.power_downstream_module1_5m + pv.power_downstream_module2_5m + pv.power_downstream_module3_5m)
        self.add_property(
            Property(self,
                     'module1u2u3_power_downstream_5m',
                     self.power_downstream_module1u2u3_5m,
                     metadata={
                         'title': 'module1 + module2 + module3 power downstream 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module1 + module2 + module3 (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1u2u3u4_5m = Value(pv.power_downstream_module1_5m + pv.power_downstream_module2_5m + pv.power_downstream_module3_5m + pv.power_downstream_module4_5m)
        self.add_property(
            Property(self,
                     'module1u2u3u4_power_downstream_5m',
                     self.power_downstream_module1u2u3u4_5m,
                     metadata={
                         'title': 'module1 + module2 + module3 + module4 power downstream 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module1 + module2 + module3 + module4 (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.power_peek_hour_utc = Value(pv.power_peak_hour_utc)
        self.add_property(
            Property(self,
                     'power_peek_hour_utc',
                     self.power_peek_hour_utc,
                     metadata={
                         'title': 'power_peek_hour_utc',
                         "type": "integer",
                         'description': 'The hour of the day when the highest PV yield was achieved (UTC)',
                         'readOnly': True,
                     }))

        self.power_peak_hour_utc = Value(pv.power_peak_hour_utc)
        self.add_property(
            Property(self,
                     'power_peak_hour_utc',
                     self.power_peak_hour_utc,
                     metadata={
                         'title': 'power_peak_hour_utc',
                         "type": "integer",
                         'description': 'The hour of the day when the highest PV yield was achieved (UTC)',
                         'readOnly': True,
                     }))

        self.latest_measurement_date = Value(pv.latest_measurement_date.strftime("%Y-%m-%dT%H:%M:%S"))
        self.add_property(
            Property(self,
                     'latest_measurement_date',
                     self.latest_measurement_date,
                     metadata={
                         'title': 'latest_measurement_date',
                         "type": "str",
                         'description': 'latest measurement date in ISO8601',
                         'readOnly': True,
                     }))


    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.power_downstream.notify_of_external_update(self.pv.power_downstream)
        self.power_downstream_5s.notify_of_external_update(self.pv.power_downstream_5s)
        self.power_downstream_15s.notify_of_external_update(self.pv.power_downstream_15s)
        self.power_downstream_1m.notify_of_external_update(self.pv.power_downstream_1m)
        self.power_downstream_5m.notify_of_external_update(self.pv.power_downstream_5m)

        self.power_downstream_module1.notify_of_external_update(self.pv.power_downstream_module1)
        self.power_downstream_module1_5s.notify_of_external_update(self.pv.power_downstream_module1_5s)
        self.power_downstream_module1_15s.notify_of_external_update(self.pv.power_downstream_module1_15s)
        self.power_downstream_module1_1m.notify_of_external_update(self.pv.power_downstream_module1_1m)
        self.power_downstream_module1_5m.notify_of_external_update(self.pv.power_downstream_module1_5m)

        self.power_downstream_module2.notify_of_external_update(self.pv.power_downstream_module2)
        self.power_downstream_module2_5s.notify_of_external_update(self.pv.power_downstream_module2_5s)
        self.power_downstream_module2_15s.notify_of_external_update(self.pv.power_downstream_module2_15s)
        self.power_downstream_module2_1m.notify_of_external_update(self.pv.power_downstream_module2_1m)
        self.power_downstream_module2_5m.notify_of_external_update(self.pv.power_downstream_module2_5m)

        self.power_downstream_module3.notify_of_external_update(self.pv.power_downstream_module3)
        self.power_downstream_module3_5s.notify_of_external_update(self.pv.power_downstream_module3_5s)
        self.power_downstream_module3_15s.notify_of_external_update(self.pv.power_downstream_module3_15s)
        self.power_downstream_module3_1m.notify_of_external_update(self.pv.power_downstream_module3_1m)
        self.power_downstream_module3_5m.notify_of_external_update(self.pv.power_downstream_module3_5m)

        self.power_downstream_module4.notify_of_external_update(self.pv.power_downstream_module4)
        self.power_downstream_module4_5s.notify_of_external_update(self.pv.power_downstream_module4_5s)
        self.power_downstream_module4_15s.notify_of_external_update(self.pv.power_downstream_module4_15s)
        self.power_downstream_module4_1m.notify_of_external_update(self.pv.power_downstream_module4_1m)
        self.power_downstream_module4_5m.notify_of_external_update(self.pv.power_downstream_module4_5m)

        self.power_downstream_module5.notify_of_external_update(self.pv.power_downstream_module5)
        self.power_downstream_module5_5s.notify_of_external_update(self.pv.power_downstream_module5_5s)
        self.power_downstream_module5_15s.notify_of_external_update(self.pv.power_downstream_module5_15s)
        self.power_downstream_module5_1m.notify_of_external_update(self.pv.power_downstream_module5_1m)
        self.power_downstream_module5_5m.notify_of_external_update(self.pv.power_downstream_module5_5m)

        self.power_downstream_module1u2_5m.notify_of_external_update(self.pv.power_downstream_module1_5m + self.pv.power_downstream_module2_5m)
        self.power_downstream_module1u2u3_5m.notify_of_external_update(self.pv.power_downstream_module1_5m + self.pv.power_downstream_module2_5m + self.pv.power_downstream_module3_5m)
        self.power_downstream_module1u2u3u4_5m.notify_of_external_update(self.pv.power_downstream_module1_5m + self.pv.power_downstream_module2_5m + self.pv.power_downstream_module3_5m + self.pv.power_downstream_module4_5m)

        self.power_peek_hour_utc.notify_of_external_update(self.pv.power_peak_hour_utc)
        self.power_peak_hour_utc.notify_of_external_update(self.pv.power_peak_hour_utc)

        self.latest_measurement_date.notify_of_external_update(self.pv.latest_measurement_date.strftime("%Y-%m-%dT%H:%M:%S"))

