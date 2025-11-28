import tornado.ioloop
import logging
from threading import Thread
from time import sleep
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from utils import WattRecorder
from shelly import ShellyMeter
from webthing import (Property, Thing, Value)
from utils import BufferedValue



class Battery:

    RESET_HOUR = 5

    def __init__(self, addr: str):
        self.__listeners = set()
        self.__is_running = True
        self.__meter = ShellyMeter.auto_select(addr, "Battery")
        self.latest_measurement_date = datetime.now(UTC)
        self.__idle_consumption = 2.4
        self.__power_discharging = 0
        self.__power_charging = 0
        self.__energy_charging_total = 0
        self.__energy_discharging_total = 0
        self.__power_charging_smoothen_recorder = WattRecorder()
        self.__power_discharging_smoothen_recorder = WattRecorder()
        self.__power_downstream_1m = BufferedValue()
        self.__power_downstream_5m = BufferedValue()

    def elapsed_since_last_measurement_sec(self):
        return (datetime.now(UTC) - self.latest_measurement_date).total_seconds()

    def add_listener(self,listener):
        self.__listeners.add(listener)


    @property
    def energy(self) -> int:
        now = datetime.now()
        today = now.date()
        offset = datetime.combine(today, time(self.RESET_HOUR))
        start = offset if now >= offset else datetime.combine(today - timedelta(days=1), time(self.RESET_HOUR))
        elapsed_hours = (now - start).total_seconds() / 3600

        idle_energy = elapsed_hours * self.__idle_consumption
        energy_uploaded =  self.__energy_charging_total - idle_energy
        if energy_uploaded < 0:
            energy_uploaded = 0

        available_energy = energy_uploaded - self.__energy_discharging_total
        if available_energy < 0:
            available_energy = 0

        energy_effective = round(available_energy * 0.86)     # efficiency round-trip  ~86%
        if energy_effective < 5:
            energy_effective = 0
        return energy_effective

    @property
    def power_upstream(self) -> int:
        return self.__power_charging

    @property
    def power_upstream_5s(self) -> int:
        return self.__power_charging_smoothen_recorder.watt_per_hour(second_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_15s(self) -> int:
        return self.__power_charging_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_1m(self) -> int:
        return self.__power_charging_smoothen_recorder.watt_per_hour(minute_range=1) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_5m(self) -> int:
        return self.__power_charging_smoothen_recorder.watt_per_hour(minute_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_upstream_60m(self) -> int:
        return self.__power_charging_smoothen_recorder.watt_per_hour(minute_range=60) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream(self) -> int:
        return self.__power_discharging_smoothen_recorder.watt_per_hour(second_range=1) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_5s(self) -> int:
        return self.__power_discharging_smoothen_recorder.watt_per_hour(second_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_15s(self) -> int:
        return self.__power_discharging_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_1m(self) -> int:
        return self.__power_downstream_1m.set_and_get(self.__power_discharging_smoothen_recorder.watt_per_hour(minute_range=1)) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def power_downstream_5m(self) -> int:
        return self.__power_downstream_5m.set_and_get(self.__power_discharging_smoothen_recorder.watt_per_hour(minute_range=5)) if self.elapsed_since_last_measurement_sec() < 60 else 0

    def __on_update(self):
        for listener in self.__listeners:
            listener()

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()
        Thread(target=self.__reset_loop, daemon=True).start()
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
                #logging.warning("error occurred on battery refresh " + str(e))
                sleep(3)

    def __reset_loop(self):
        while self.__is_running:
            try:
                hour = datetime.now().hour
                if hour == self.RESET_HOUR:
                    # reset uploaded energy counter at 5 am (energy should be consumed meanwhile)
                    logging.info("counter reset")
                    self.__meter.reset_counter()
                sleep(10*60)
            except Exception as e:
                sleep(3)

    def __measure(self):
        m = self.__meter.measure()
        power = m.total
        self.__energy_charging_total = m.energy_total
        self.__energy_discharging_total = m.ret_energy_total

        self.__power_discharging = 0 if power >= 0 else (power*-1)                    # negative power -> battery discharging
        self.__power_charging = 0 if power <= self.__idle_consumption else power      # positive power -> battery charging

        self.__power_charging_smoothen_recorder.put(self.__power_charging)
        self.__power_discharging_smoothen_recorder.put(self.__power_discharging)

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
        if self.power_upstream > 3:
            state = 'charging with ' + str(int(self.power_upstream)) + 'W'
        elif self.power_downstream > 3:
            state = 'discharging with ' + str(int(self.power_downstream)) + 'W'
        else:
            state = 'idling'

        return "Battery " + str(int(self.energy)) + "W (" + state + ")"



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


        self.energy = Value(battery.energy)
        self.add_property(
            Property(self,
                     'energy',
                     self.energy,
                     metadata={
                         'title': 'energy',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the available battery power',
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

        self.energy.notify_of_external_update(self.battery.energy)

'''
b = Battery("http://10.1.33.100")
b.start()
sleep(2)

while True:
    print("energy " + str(b.energy))
    sleep(5)
'''