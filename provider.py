import tornado.ioloop
import logging
from threading import Thread
from datetime import datetime
from time import sleep
from webthing import (Property, Thing, Value)
from shelly import ShellyMeter
from utils import WattRecorder



class Provider:

    def __init__(self, meter_addr_provider: str):
        self.__is_running = True
        self.__listeners = set()

        self.__provider_shelly = ShellyMeter(meter_addr_provider, "Meter provider")
        self.name = self.__provider_shelly.info().name
        self.provider_power = 0
        self.provider_power_downstream = 0
        self.provider_power_upstream = 0

        self.latest_measurement_date = datetime.now()

        self.__provider_power_smoothen_recorder = WattRecorder()
        self.__provider_power_downstream_smoothen_recorder = WattRecorder()
        self.__provider_power_upstream_smoothen_recorder = WattRecorder()

    def elapsed_since_last_measurement_sec(self):
        return (datetime.now() - self.latest_measurement_date).total_seconds()

    @property
    def provider_power_5s(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def provider_power_15s(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def provider_power_1m(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def provider_power_5m(self) -> int:
        return self.__provider_power_smoothen_recorder.watt_per_hour(minute_range=5)

    @property
    def provider_power_downstream_5s(self) -> int:
        return self.__provider_power_downstream_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def provider_power_downstream_15s(self) -> int:
        return self.__provider_power_downstream_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def provider_power_downstream_1m(self) -> int:
        return self.__provider_power_downstream_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def provider_power_downstream_5m(self) -> int:
        return self.__provider_power_downstream_smoothen_recorder.watt_per_hour(minute_range=5)

    @property
    def provider_power_upstream_5s(self) -> int:
        return self.__provider_power_upstream_smoothen_recorder.watt_per_hour(second_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def provider_power_upstream_15s(self) -> int:
        return self.__provider_power_upstream_smoothen_recorder.watt_per_hour(second_range=15) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def provider_power_upstream_1m(self) -> int:
        return self.__provider_power_upstream_smoothen_recorder.watt_per_hour(minute_range=1) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def provider_power_upstream_5m(self) -> int:
        return self.__provider_power_upstream_smoothen_recorder.watt_per_hour(minute_range=5) if self.elapsed_since_last_measurement_sec() < 60 else 0

    @property
    def provider_power_upstream_60m(self) -> int:
        return self.__provider_power_upstream_smoothen_recorder.watt_per_hour(minute_range=60) if self.elapsed_since_last_measurement_sec() < 60 else 0


    def add_listener(self,listener):
        self.__listeners.add(listener)

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()
        Thread(target=self.__info_loop, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __measure_loop(self):
        while self.__is_running:
            try:
                self.__measure()
                self.latest_measurement_date = datetime.now()
                [listener() for listener in self.__listeners]
                sleep(1.03)
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
                sleep(3)

    def __measure(self):
        power = self.__provider_shelly.measure().total
        downstream_power = 0 if power < 0 else power
        upstream_power = 0 if power > 0 else (power*-1)

        self.provider_power = power
        self.provider_power_downstream = downstream_power
        self.provider_power_upstream = upstream_power

        self.__provider_power_smoothen_recorder.put(power)
        self.__provider_power_downstream_smoothen_recorder.put(downstream_power)
        self.__provider_power_upstream_smoothen_recorder.put(upstream_power)

    def __info_loop(self):
        sleep(3 * 60)
        while self.__is_running:
            try:
                logging.info(self.__info())
                sleep(10*60)
            except Exception as e:
                logging.warning("error occurred on info " + str(e))
                sleep(4 * 60)

    def __info(self) -> str:
        return "Provider " + str(int(self.provider_power_1m)) + "W - last measurement: " + self.latest_measurement_date.strftime("%H:%M")






class ProviderThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, provider: Provider):
        Thing.__init__(
            self,
            'urn:dev:ops:energy-provider',
            'EnergySensor',
            ['MultiLevelSensor'],
            "energy provider"
        )
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.provider = provider
        self.provider.add_listener(self.on_value_changed)


        self.provider_power = Value(provider.provider_power)
        self.add_property(
            Property(self,
                     'power',
                     self.provider_power,
                     metadata={
                         'title': 'provider_power',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the provider (may be negative)',
                         'readOnly': True,
                     }))

        self.provider_power_5s = Value(provider.provider_power_5s)
        self.add_property(
            Property(self,
                     'power_5s',
                     self.provider_power_5s,
                     metadata={
                         'title': 'power_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.provider_power_15s = Value(provider.provider_power_15s)
        self.add_property(
            Property(self,
                     'power_15s',
                     self.provider_power_15s,
                     metadata={
                         'title': 'provider_power_15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 15 sec)',
                         'readOnly': True,
                     }))


        self.provider_power_1m = Value(provider.provider_power_1m)
        self.add_property(
            Property(self,
                     'power_1m',
                     self.provider_power_1m,
                     metadata={
                         'title': 'provider_power_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 1 mim)',
                         'readOnly': True,
                     }))


        self.provider_power_5m = Value(provider.provider_power_5m)
        self.add_property(
            Property(self,
                     'power_5m',
                     self.provider_power_5m,
                     metadata={
                         'title': 'provider_power_5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.provider_power_downstream = Value(provider.provider_power_downstream)
        self.add_property(
            Property(self,
                     'power_downstream',
                     self.provider_power_downstream,
                     metadata={
                         'title': 'provider_power_downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current downstream power of the provider',
                         'readOnly': True,
                     }))

        self.provider_power_downstream_5s = Value(provider.provider_power_downstream_5s)
        self.add_property(
            Property(self,
                     'power_downstream_5s',
                     self.provider_power_downstream_5s,
                     metadata={
                         'title': 'provider_power_downstream_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the downstream power provider  (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.provider_power_downstream_15s = Value(provider.provider_power_downstream_15s)
        self.add_property(
            Property(self,
                     'power_downstream_15s',
                     self.provider_power_downstream_15s,
                     metadata={
                         'title': 'provider_power_downstream_15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the downstream power provider  (smoothen 15 sec)',
                         'readOnly': True,
                     }))


        self.provider_power_downstream_1m = Value(provider.provider_power_downstream_1m)
        self.add_property(
            Property(self,
                     'power_downstream_1m',
                     self.provider_power_downstream_1m,
                     metadata={
                         'title': 'provider_power_downstream_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the downstream power provider  (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.provider_power_downstream_5m = Value(provider.provider_power_downstream_5m)
        self.add_property(
            Property(self,
                     'power_downstream_5m',
                     self.provider_power_downstream_5m,
                     metadata={
                         'title': 'provider_power_downstream_5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the downstream power provider  (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.provider_power_upstream = Value(provider.provider_power_upstream)
        self.add_property(
            Property(self,
                     'power_upstream',
                     self.provider_power_upstream,
                     metadata={
                         'title': 'provider_power_upstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current upstream power of the provider',
                         'readOnly': True,
                     }))

        self.provider_power_upstream_5s = Value(provider.provider_power_upstream_5s)
        self.add_property(
            Property(self,
                     'power_upstream_5s',
                     self.provider_power_upstream_5s,
                     metadata={
                         'title': 'provider_power_upstream_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the upstream power provider  (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.provider_power_upstream_15s = Value(provider.provider_power_upstream_15s)
        self.add_property(
            Property(self,
                     'power_upstream_15s',
                     self.provider_power_upstream_15s,
                     metadata={
                         'title': 'provider_power_upstream_15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the upstream power provider  (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.provider_power_upstream_15s = Value(provider.provider_power_upstream_15s)
        self.add_property(
            Property(self,
                     'power_upstream_15s',
                     self.provider_power_upstream_15s,
                     metadata={
                         'title': 'provider_power_upstream_15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the upstream power provider  (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.provider_power_upstream_1m = Value(provider.provider_power_upstream_1m)
        self.add_property(
            Property(self,
                     'power_upstream_1m',
                     self.provider_power_upstream_1m,
                     metadata={
                         'title': 'provider_power_upstream_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the upstream power provider  (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.provider_power_upstream_5m = Value(provider.provider_power_upstream_5m)
        self.add_property(
            Property(self,
                     'power_upstream_5m',
                     self.provider_power_upstream_5m,
                     metadata={
                         'title': 'provider_power_upstream_5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the upstream power provider  (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.latest_measurement_date = Value(provider.latest_measurement_date.strftime("%Y-%m-%dT%H:%M:%S"))
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
        self.provider_power.notify_of_external_update(self.provider.provider_power)
        self.provider_power_5s.notify_of_external_update(self.provider.provider_power_5s)
        self.provider_power_15s.notify_of_external_update(self.provider.provider_power_15s)
        self.provider_power_1m.notify_of_external_update(self.provider.provider_power_1m)
        self.provider_power_5m.notify_of_external_update(self.provider.provider_power_5m)

        self.provider_power_downstream.notify_of_external_update(self.provider.provider_power_downstream)
        self.provider_power_downstream_5s.notify_of_external_update(self.provider.provider_power_downstream_5s)
        self.provider_power_downstream_15s.notify_of_external_update(self.provider.provider_power_downstream_15s)
        self.provider_power_downstream_1m.notify_of_external_update(self.provider.provider_power_downstream_1m)
        self.provider_power_downstream_5m.notify_of_external_update(self.provider.provider_power_downstream_5m)

        self.provider_power_upstream.notify_of_external_update(self.provider.provider_power_upstream)
        self.provider_power_upstream_5s.notify_of_external_update(self.provider.provider_power_upstream_5s)
        self.provider_power_upstream_15s.notify_of_external_update(self.provider.provider_power_upstream_15s)
        self.provider_power_upstream_1m.notify_of_external_update(self.provider.provider_power_upstream_1m)
        self.provider_power_upstream_5m.notify_of_external_update(self.provider.provider_power_upstream_5m)

        self.latest_measurement_date.notify_of_external_update(self.provider.latest_measurement_date.strftime("%Y-%m-%dT%H:%M:%S"))

