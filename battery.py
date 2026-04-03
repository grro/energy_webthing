import tornado.ioloop
import logging
from threading import Thread
from time import sleep
from typing import List
from datetime import UTC, datetime, timedelta, date
from utils import WattRecorder
from shelly import ShellyMeter
from redzoo.database.simple import SimpleDB
from webthing import (Property, Thing, Value)
from utils import BufferedValue
from battery_mqtt import PvMqtt



class Battery:

    def __init__(self, addr: str, directory: str, mqtt_addr):
        self.__energy_down_per_day = SimpleDB("battery_down", sync_period_sec=60, directory=directory)
        self.__daily_counter = SimpleDB("battery_daily_counter", sync_period_sec=60, directory=directory)
        self.__listeners = set()
        self.__is_running = True
        self.__meter = ShellyMeter.auto_select(addr, "Battery")
        self.latest_measurement_date = datetime.now(UTC)
        self.__power_discharging = 0
        self.__power_charging = 0
        self.__power_charging = 0
        self.__power_charging_smoothen_recorder = WattRecorder()
        self.__power_discharging_smoothen_recorder = WattRecorder()
        self.__power = BufferedValue()
        self.__power_downstream_1m = BufferedValue()
        self.__power_downstream_5m = BufferedValue()
        self.__show_total_status = True
        self.__mqtt = PvMqtt(mqtt_addr)
        self.__mqtt.add_listener(self.__notify_listeners)

    @property
    def __today(self) -> str:
        return str(datetime.now().timetuple().tm_yday)

    @property
    def __yesterday(self) -> str:
        return str((datetime.now() - timedelta(days=1)).timetuple().tm_yday)

    @property
    def __tomorrow(self) -> str:
        return str((datetime.now() + timedelta(days=1)).timetuple().tm_yday)

    def elapsed_since_last_measurement_sec(self):
        return (datetime.now(UTC) - self.latest_measurement_date).total_seconds()

    def add_listener(self,listener):
        self.__listeners.add(listener)

    @property
    def __energy_idle_consumption_today(self) -> int:
        elapsed_hours_today = datetime.now().hour
        idle_consumption = elapsed_hours_today * 3.8  # idle consumption
        return round(idle_consumption)

    def __seconds_of_day(self) -> int:
        now = datetime.now()
        return now.hour * 3600 + now.minute * 60 + now.second

    @property
    def status(self) -> str:
        if self.power_upstream_5s > 0:
            pwr = str(round(self.state_of_charge, 1)) + "% (laden)"
        elif self.power_upstream_5s > 0 or self.power_downstream_5s > 0:
            pwr = str(round(self.state_of_charge, 1)) + "% (entladen)"
        else:
            pwr = str(round(self.state_of_charge, 1)) + "%"
        return pwr

    @property
    def state_of_charge(self) -> float:
        return self.__mqtt.state_of_charge

    @property
    def power(self) -> int:
        return self.__power.set_and_get(self.power_upstream if self.power_upstream > 0 else (self.power_downstream * -1))

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

    def __energy_down_current_year_list_raw(self, last_day:int = 365) -> List[int]:
        return [self.__energy_down_per_day.get(str(day_of_year), None) for day_of_year in range(0, last_day)]

    @property
    def __energy_down_start_day(self) -> date:
        down_per_day = self.__energy_down_current_year_list_raw(365)
        for day in range(0,365):
            if down_per_day[day] is not None and  down_per_day[day] >= 0:
                return (datetime(datetime.now().year, 1, 1, tzinfo=UTC) + timedelta(days=day)).date()
        return datetime.now().date()

    @property
    def __energy_down_end_day(self) -> date:
        down_per_day = self.__energy_down_current_year_list_raw(365)
        for day in range(364, -1, -1):
            if down_per_day[day] is not None and  down_per_day[day] >= 0:
                return (datetime(datetime.now().year, 1, 1, tzinfo=UTC) + timedelta(days=day)).date()
        return datetime.now().date()

    def __energy_down_current_year_list(self, last_day:int = 365) -> List[int]:
        down_per_day = self.__energy_down_current_year_list_raw(last_day)
        down_list = [green for green in down_per_day if green is not None]
        down_list = [green for green in down_list if green >= 0]
        return down_list

    @property
    def energy_down_current_year(self) -> int:
        current_day = int(datetime.now().strftime('%j'))
        return sum(self.__energy_down_current_year_list(current_day))

    @property
    def energy_down_estimated_year(self) -> int:
        down_per_day = self.__energy_down_current_year_list(365)
        if len(down_per_day) > 0:
            return int(sum(down_per_day) * 365 / len(down_per_day))
        else:
            return 0

    @property
    def energy_down_today(self) -> int:
        return round(self.__energy_discharged_today)

    def __notify_listeners(self):
        for listener in self.__listeners:
            listener()

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()
        Thread(target=self.__info_loop, daemon=True).start()
        Thread(target=self.__history_loop, daemon=True).start()
        Thread(target=self.__mqtt.start, daemon=True).start()

    def stop(self):
        self.__is_running = False
        self.__mqtt.stop()

    def __measure_loop(self):
        while self.__is_running:
            try:
                self.__measure()
                [listener() for listener in self.__listeners]
                self.latest_measurement_date = datetime.now(UTC)
                sleep(3.03)
            except Exception as e:
                #logging.warning("error occurred on battery refresh " + str(e))
                sleep(3)

    def __history_loop(self):
        sleep(15)
        while self.__is_running:
            try:
                self.__energy_down_per_day.put(self.__today, self.__energy_discharged_today)
                self.__energy_down_per_day.put(self.__tomorrow, -9999)
            except Exception as e:
                logging.warning("error occurred on history " + str(e))
            sleep(3*60)

    def __measure(self):
        m = self.__meter.measure()

        self.__daily_counter.put("total_"+ self.__today, m.energy_total, ttl_sec=7*24*60*60)
        self.__daily_counter.put("return_total_"+ self.__today, m.ret_energy_total, ttl_sec=7*24*60*60)

        power = m.total
        self.__power_discharging = 0 if power >= 0 else (power*-1)                    # negative power -> battery discharging
        self.__power_charging = 0 if power <= 4 else power                            # positive power -> battery charging

        self.__power_charging_smoothen_recorder.put(self.__power_charging)
        self.__power_discharging_smoothen_recorder.put(self.__power_discharging)

    @property
    def __energy_charged_today(self) -> int:
        counter_today = self.__daily_counter.get("total_" + self.__today, default_value=0)
        counter_yesterday = self.__daily_counter.get("total_" + self.__yesterday, counter_today)
        return round(counter_today - counter_yesterday)

    @property
    def __energy_discharged_today(self) -> int:
        counter_today = self.__daily_counter.get("return_total_" + self.__today, default_value=0)
        counter_yesterday = self.__daily_counter.get("return_total_" + self.__yesterday, counter_today)
        return round(counter_today - counter_yesterday)

    def __info_loop(self):
        sleep(10)
        while self.__is_running:
            try:
                logging.info(self.__info())
                sleep(5*60)
            except Exception as e:
                logging.warning("error occurred on info " + str(e))
                sleep(4 * 60)

    def __info(self) -> str:
        if self.power_upstream > 3:
            state =  str(self.state_of_charge) + '% charging with ' + str(int(self.power_upstream)) + 'W'
        elif self.power_downstream > 3:
            state =  str(self.state_of_charge) + '% discharging with ' + str(int(self.power_downstream)) + 'W'
        else:
            state =  str(self.state_of_charge) + "% (idling)"

        return "Battery level " + state



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
                         'description': 'the current battery power  ma be negative (discharging)',
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

        self.energy_down_today = Value(battery.energy_down_today)
        self.add_property(
            Property(self,
                     'energy_down_today',
                     self.energy_down_today,
                     metadata={
                         'title': 'energy down today',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the downstream battery power today  (unloading)',
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

        self.state_of_charge = Value(battery.state_of_charge)
        self.add_property(
            Property(self,
                     'charge_level',
                     self.state_of_charge,
                     metadata={
                         'title': 'charge_level',
                         "type": "integer",
                         'unit': 'percent',
                         'description': 'the battery charge level',
                         'readOnly': True,
                     }))

        self.status = Value(battery.status)
        self.add_property(
            Property(self,
                     'status',
                     self.status,
                     metadata={
                         'title': 'status',
                         "type": "string",
                         'description': 'the battery status',
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
        self.status.notify_of_external_update(self.battery.status)

        self.energy_down_today.notify_of_external_update(self.battery.energy_down_today)
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

        self.state_of_charge.notify_of_external_update(self.battery.state_of_charge)



