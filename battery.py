import tornado.ioloop
import logging
from threading import Thread
from time import sleep
from datetime import datetime
from utils import WattRecorder
from shelly import ShellyMeter
from webthing import (Property, Thing, Value)
from utils import BufferedValue



class EnergySource:

    def __init__(self):
        self.__is_running = True
        self.__unloading_counter_by_hour = {}
        self.__loading_counter_by_hour = {}
        self.__energy_wh = 0

    def add(self, counter_loading: int, counter_unloading: int):
        hour = datetime.now().hour
        self.__unloading_counter_by_hour[hour] = counter_unloading
        self.__loading_counter_by_hour[hour] = counter_loading

    @property
    def energy_wh(self) -> int:
        return self.__energy_wh

    def start(self):
        Thread(target=self.__compute_energy_loop, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __compute_energy_loop(self):
        while self.__is_running:
            try:
                hour_now = datetime.now().hour

                loading_counter_now = self.__loading_counter_by_hour.get(hour_now, 0)
                loading_counter_4am =  self.__loading_counter_by_hour.get(4, loading_counter_now)
                loading_counter_current_day = loading_counter_now - loading_counter_4am

                unloading_counter_now = self.__unloading_counter_by_hour.get(hour_now, 0)
                unloading_counter_4am =  self.__unloading_counter_by_hour.get(4, unloading_counter_now)
                unloading_counter_current_day = unloading_counter_now - unloading_counter_4am

                energy_current_day = loading_counter_current_day - unloading_counter_current_day
                self.__energy_wh  = 0 if energy_current_day < 0 else energy_current_day
            except Exception as e:
                 logging.warning(str(e))
            sleep(7)


class Battery:

    def __init__(self, addr: str):
        self.__listeners = set()
        self.__is_running = True
        self.__meter = ShellyMeter.auto_select(addr, "Battery")
        self.latest_measurement_date = datetime.now()
        self.__power = 0
        self.__power_unloading = 0
        self.__power_loading= 0
        self.__power_smoothen_recorder = WattRecorder()
        self.__power_unloading_smoothen_recorder = WattRecorder()
        self.__power_loading_smoothen_recorder = WattRecorder()
        self.__energy = EnergySource()
        self.__energy_wh = BufferedValue()
        self.__power_downstream_1m = BufferedValue()
        self.__power_downstream_5m = BufferedValue()

    def elapsed_since_last_measurement_sec(self):
        return (datetime.now() - self.latest_measurement_date).total_seconds()

    def add_listener(self,listener):
        self.__listeners.add(listener)

    @property
    def energy_wh(self) -> int:
        return self.__energy_wh.set_and_get(self.__energy.energy_wh)  if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power(self) -> int:
        return self.__power if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_5s(self) -> int:
        return self.__power_smoothen_recorder.watt_per_hour(second_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_15s(self) -> int:
        return self.__power_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_1m(self) -> int:
        return self.__power_smoothen_recorder.watt_per_hour(minute_range=1) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_5m(self) -> int:
        return self.__power_smoothen_recorder.watt_per_hour(minute_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream(self) -> int:
        return self.__power_loading

    @property
    def power_upstream_5s(self) -> int:
        return self.__power_loading_smoothen_recorder.watt_per_hour(second_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_15s(self) -> int:
        return self.__power_loading_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_1m(self) -> int:
        return self.__power_loading_smoothen_recorder.watt_per_hour(minute_range=1) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_5m(self) -> int:
        return self.__power_loading_smoothen_recorder.watt_per_hour(minute_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_60m(self) -> int:
        return self.__power_loading_smoothen_recorder.watt_per_hour(minute_range=60) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream(self) -> int:
        return self.__power_unloading_smoothen_recorder.watt_per_hour(second_range=1) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_5s(self) -> int:
        return self.__power_unloading_smoothen_recorder.watt_per_hour(second_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_15s(self) -> int:
        return self.__power_unloading_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_1m(self) -> int:
        return self.__power_downstream_1m.set_and_get(self.__power_unloading_smoothen_recorder.watt_per_hour(minute_range=1)) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_5m(self) -> int:
        return self.__power_downstream_5m.set_and_get(self.__power_unloading_smoothen_recorder.watt_per_hour(minute_range=5)) if self.elapsed_since_last_measurement_sec() < 60 else 0

    def __on_update(self):
        for listener in self.__listeners:
            listener()

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()
        self.__energy.start()

    def stop(self):
        self.__is_running = False
        self.__energy.stop()

    def __measure_loop(self):
        while self.__is_running:
            try:
                self.__measure()
                self.latest_measurement_date = datetime.now()
                [listener() for listener in self.__listeners]
                sleep(1.03)
            except Exception as e:
                #logging.warning("error occurred on battery refresh " + str(e))
                sleep(3)

    def __measure(self):
        m = self.__meter.measure()
        power = m.total
        if -3 < power < 3:  # ignore low values
            power = 0
        self.__power = power                                          # battery -> energy source
        self.__power_unloading = 0 if power < 0 else power            #  positive power -> battery unloads
        self.__power_loading = 0 if power > 0 else (power*-1)         #  negative power -> battery loads

        self.__power_smoothen_recorder.put(self.__power)
        self.__power_loading_smoothen_recorder.put(self.__power_loading)
        self.__power_unloading_smoothen_recorder.put(self.__power_unloading)
        self.__energy.add(m.energy_total, m.ret_energy_total)

    def __info_loop(self):
        sleep(1 * 60)
        while self.__is_running:
            try:
                logging.info(self.__info())
                sleep(10*60)
            except Exception as e:
                logging.warning("error occurred on info " + str(e))
                sleep(4 * 60)

    def __info(self) -> str:
        return "(1m smoothen) Battery " + str(int(self.power_1m)) + "W; measured at " + self.latest_measurement_date.strftime("%H:%M")



class BatteryThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, battery: Battery):
        Thing.__init__(
            self,
            'urn:dev:ops:battery-1',
            'EnergySensor',
            ['MultiLevelSensor'],
            "battery"
        )
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.battery = battery
        self.battery.add_listener(self.on_value_changed)


        self.power = Value(battery.power)
        self.add_property(
            Property(self,
                     'power',
                     self.power,
                     metadata={
                         'title': 'power',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the battery power (may be negative by loading)',
                         'readOnly': True,
                     }))

        self.power_5s = Value(battery.power_5s)
        self.add_property(
            Property(self,
                     'power_5s',
                     self.power_5s,
                     metadata={
                         'title': 'power 5 sec',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the battery power (may be negative by loading; smoothen over 5 sec)',
                         'readOnly': True,
                     }))

        self.power_15s = Value(battery.power_15s)
        self.add_property(
            Property(self,
                     'power_15s',
                     self.power_15s,
                     metadata={
                         'title': 'power 15 sec',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the battery power (may be negative by loading; smoothen over 15 sec)',
                         'readOnly': True,
                     }))

        self.power_1m = Value(battery.power_1m)
        self.add_property(
            Property(self,
                     'power_1m',
                     self.power_1m,
                     metadata={
                         'title': 'power 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the battery power (may be negative by loading; smoothen over 1 min)',
                         'readOnly': True,
                     }))

        self.power_5m = Value(battery.power_5m)
        self.add_property(
            Property(self,
                     'power_5m',
                     self.power_5m,
                     metadata={
                         'title': 'power 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the battery power (may be negative by loading; smoothen over 5 min)',
                         'readOnly': True,
                     }))

        self.power_upstream = Value(battery.power_upstream)
        self.add_property(
            Property(self,
                     'power_upstream',
                     self.power_upstream,
                     metadata={
                         'title': 'power upstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current upstream battery power (loading)',
                         'readOnly': True,
                     }))

        self.power_upstream_5s = Value(battery.power_upstream_5s)
        self.add_property(
            Property(self,
                     'power_upstream_5s',
                     self.power_upstream_5s,
                     metadata={
                         'title': 'power upstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the smoothen upstream battery power (loading) over 5 seconds',
                         'readOnly': True,
                     }))

        self.power_upstream_15s = Value(battery.power_upstream_15s)
        self.add_property(
            Property(self,
                     'power_upstream_15s',
                     self.power_upstream_15s,
                     metadata={
                         'title': 'power upstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the smoothen upstream battery power (loading) over 15 seconds',
                         'readOnly': True,
                     }))

        self.power_upstream_1m = Value(battery.power_upstream_1m)
        self.add_property(
            Property(self,
                     'power_upstream_1m',
                     self.power_upstream_1m,
                     metadata={
                         'title': 'power upstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the smoothen upstream battery power (loading) over 1 minutes',
                         'readOnly': True,
                     }))

        self.power_upstream_5m = Value(battery.power_upstream_5m)
        self.add_property(
            Property(self,
                     'power_upstream_5m',
                     self.power_upstream_5m,
                     metadata={
                         'title': 'power upstream 5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the smoothen upstream battery power (loading) over 5 minutes',
                         'readOnly': True,
                     }))

        self.power_downstream = Value(battery.power_downstream)
        self.add_property(
            Property(self,
                     'power_downstream',
                     self.power_downstream,
                     metadata={
                         'title': 'power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current downstream battery power (unloading)',
                         'readOnly': True,
                     }))

        self.power_downstream_5s = Value(battery.power_downstream_5s)
        self.add_property(
            Property(self,
                     'power_downstream_5s',
                     self.power_downstream_5s,
                     metadata={
                         'title': 'power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current downstream battery power (unloading) smoothen over 5 seconds',
                         'readOnly': True,
                     }))

        self.power_downstream_15s = Value(battery.power_downstream_15s)
        self.add_property(
            Property(self,
                     'power_downstream_15s',
                     self.power_downstream_15s,
                     metadata={
                         'title': 'power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current downstream battery power (unloading) smoothen over 15 seconds',
                         'readOnly': True,
                     }))

        self.power_downstream_1m = Value(battery.power_downstream_1m)
        self.add_property(
            Property(self,
                     'power_downstream_1m',
                     self.power_downstream_1m,
                     metadata={
                         'title': 'power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current downstream battery power (unloading) smoothen over 1 minute',
                         'readOnly': True,
                     }))


        self.power_downstream_5m = Value(battery.power_downstream_5m)
        self.add_property(
            Property(self,
                     'power_downstream_5m',
                     self.power_downstream_5m,
                     metadata={
                         'title': 'power downstream 5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current downstream battery power (unloading) smoothen over 5 minute',
                         'readOnly': True,
                     }))


        self.energy_wh = Value(battery.energy_wh)
        self.add_property(
            Property(self,
                     'energy_wh',
                     self.energy_wh,
                     metadata={
                         'title': 'energy',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the battery power (watt per hour)',
                         'readOnly': True,
                     }))

        self.latest_measurement_date = Value(battery.latest_measurement_date.strftime("%Y-%m-%dT%H:%M:%S"))
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
        self.power.notify_of_external_update(self.battery.power)
        self.power_5s.notify_of_external_update(self.battery.power_5m)
        self.power_15s.notify_of_external_update(self.battery.power_15s)
        self.power_downstream_1m.notify_of_external_update(self.battery.power_downstream_1m)
        self.power_downstream_5m.notify_of_external_update(self.battery.power_downstream_5m)

        self.power_upstream.notify_of_external_update(self.battery.power_upstream)
        self.power_upstream_5s.notify_of_external_update(self.battery.power_upstream_5s)
        self.power_upstream_15s.notify_of_external_update(self.battery.power_upstream_15s)
        self.power_upstream_1m.notify_of_external_update(self.battery.power_upstream_1m)
        self.power_upstream_5m.notify_of_external_update(self.battery.power_upstream_5m)

        self.power_downstream.notify_of_external_update(self.battery.power_downstream)
        self.power_downstream_5s.notify_of_external_update(self.battery.power_downstream_5s)
        self.power_downstream_15s.notify_of_external_update(self.battery.power_downstream_15s)
        self.power_downstream_1m.notify_of_external_update(self.battery.power_downstream_1m)
        self.power_downstream_5m.notify_of_external_update(self.battery.power_downstream_5m)

        self.latest_measurement_date.notify_of_external_update(self.battery.latest_measurement_date.strftime("%Y-%m-%dT%H:%M:%S"))

        self.energy_wh.notify_of_external_update(self.battery.energy_wh)

'''
b = Battery("http://10.1.33.94")
b.start()
sleep(2)

while True:
    print("energy " + str(b.energy_wh))
    sleep(5)
'''