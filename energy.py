import logging
import tornado.ioloop
from webthing import (Property, Thing, Value)
from provider import Provider
from pv import Pv
from battery import Battery
from threading import Thread
from time import sleep
from datetime import datetime



class Energy:

    def __init__(self, provider: Provider, pv: Pv, battery: Battery):
        self.__is_running = True
        self.__listeners = set()
        self.provider = provider
        self.pv = pv
        self.battery = battery
        self.provider.add_listener(self.__on_update)
        self.pv.add_listener(self.__on_update)
        self.battery.add_listener(self.__on_update)
        self.__power_consumption_5m = 0

    @property
    def power_consumption(self) -> int:
        # energy source
        #   provider: may be negative by uploading surplus
        #   battery: may be negative by loading
        #   pv: positive only by producing
        return self.provider.provider_power + self.battery.power + self.pv.power_downstream

    @property
    def power_consumption_5s(self) -> int:
        return self.provider.provider_power_5s + self.battery.power_5s + self.pv.power_downstream_5s

    @property
    def power_consumption_15s(self) -> int:
        return self.provider.provider_power_5s + self.battery.power_15s + self.pv.power_downstream_15s

    @property
    def power_consumption_1m(self) -> int:
        return self.provider.provider_power_1m + self.battery.power_1m + self.pv.power_downstream_1m

    @property
    def power_consumption_5m(self) -> int:
        return self.__power_consumption_5m

    def __power_consumption_5m_loop(self):
        while self.__is_running:
            try:
                self.__power_consumption_5m = self.provider.provider_power_5m + self.battery.power_5m + self.pv.power_downstream_5m
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
            sleep(4.07)

    @property
    def power_surplus(self) -> int:
        return self.provider.provider_power_upstream + self.battery.power_upstream

    @property
    def power_surplus_5s(self) -> int:
        return self.provider.provider_power_upstream_5s + self.battery.power_upstream_5s

    @property
    def power_surplus_15s(self) -> int:
        return self.provider.provider_power_upstream_15s + self.battery.power_upstream_15s

    @property
    def power_surplus_1m(self) -> int:
        return self.provider.provider_power_upstream_1m + self.battery.power_upstream_1m

    @property
    def power_surplus_5m(self) -> int:
        return self.provider.provider_power_upstream_5m + self.battery.power_upstream_5m

    @property
    def power_surplus_60m(self) -> int:
        return self.provider.provider_power_upstream_60m + self.battery.power_upstream_60m

    def __on_update(self):
        [listener() for listener in self.__listeners]

    def add_listener(self, listener):
        self.__listeners.add(listener)

    def start(self):
        Thread(target=self.__power_consumption_5m_loop, daemon=True).start()

    def stop(self):
        self.__is_running = False



class EnergyThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, energy: Energy):
        Thing.__init__(
            self,
            'urn:dev:ops:energy-3',
            'EnergySensor',
            ['MultiLevelSensor'],
            "energy"
        )
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.energy = energy
        self.energy.add_listener(self.on_value_changed)

        self.power_surplus = Value(energy.power_surplus)
        self.add_property(
            Property(self,
                     'power_surplus',
                     self.power_surplus,
                     metadata={
                         'title': 'power surplus',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current surplus pv power (provider upstream + battery loading upstream)',
                         'readOnly': True,
                     }))

        self.power_surplus_5s = Value(energy.power_surplus_5s)
        self.add_property(
            Property(self,
                     'power_surplus_5s',
                     self.power_surplus_5s,
                     metadata={
                         'title': 'power surplus 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the surplus pv power (provider upstream + battery loading upstream) smoothen over 5 seconds',
                         'readOnly': True,
                     }))

        self.power_surplus_15s = Value(energy.power_surplus_15s)
        self.add_property(
            Property(self,
                     'power_surplus_15s',
                     self.power_surplus_15s,
                     metadata={
                         'title': 'power surplus 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the surplus pv power (provider upstream + battery loading upstream) smoothen over 15 seconds',
                         'readOnly': True,
                     }))

        self.power_surplus_1m = Value(energy.power_surplus_1m)
        self.add_property(
            Property(self,
                     'power_surplus_1m',
                     self.power_surplus_1m,
                     metadata={
                         'title': 'power surplus 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the surplus pv power (provider upstream + battery loading upstream) smoothen over 1 minute',
                         'readOnly': True,
                     }))


        self.power_surplus_5m = Value(energy.power_surplus_5m)
        self.add_property(
            Property(self,
                     'power_surplus_5m',
                     self.power_surplus_5m,
                     metadata={
                         'title': 'power surplus 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the surplus pv power (provider upstream + battery loading upstream) smoothen over 5 minute',
                         'readOnly': True,
                     }))

        self.power_consumption = Value(energy.power_consumption)
        self.add_property(
            Property(self,
                     'power_consumption',
                     self.power_consumption,
                     metadata={
                         'title': 'power consumption',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power consumption',
                         'readOnly': True,
                     }))

        self.power_consumption_5s = Value(energy.power_consumption_5s)
        self.add_property(
            Property(self,
                     'power_consumption_5s',
                     self.power_consumption_5s,
                     metadata={
                         'title': 'power consumption 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power consumption smoothen over 5 seconds',
                         'readOnly': True,
                     }))

        self.power_consumption_15s = Value(energy.power_consumption_15s)
        self.add_property(
            Property(self,
                     'power_consumption_15s',
                     self.power_consumption_15s,
                     metadata={
                         'title': 'power consumption 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power consumption smoothen over 15 seconds',
                         'readOnly': True,
                     }))


        self.power_consumption_1m = Value(energy.power_consumption_1m)
        self.add_property(
            Property(self,
                     'power_consumption_1m',
                     self.power_consumption_1m,
                     metadata={
                         'title': 'power consumption 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power consumption smoothen over 1 minute',
                         'readOnly': True,
                     }))

        self.power_consumption_5m = Value(energy.power_consumption_5m)
        self.add_property(
            Property(self,
                     'power_consumption_5m',
                     self.power_consumption_5m,
                     metadata={
                         'title': 'power consumption 5 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power consumption smoothen over 5 minute',
                         'readOnly': True,
                     }))


    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.power_surplus.notify_of_external_update(self.energy.power_surplus)
        self.power_surplus_5s.notify_of_external_update(self.energy.power_surplus_5s)
        self.power_surplus_15s.notify_of_external_update(self.energy.power_surplus_15s)
        self.power_surplus_1m.notify_of_external_update(self.energy.power_surplus_1m)
        self.power_surplus_5m.notify_of_external_update(self.energy.power_surplus_5m)

        self.power_consumption.notify_of_external_update(self.energy.power_consumption)
        self.power_consumption_5s.notify_of_external_update(self.energy.power_consumption_5s)
        self.power_consumption_15s.notify_of_external_update(self.energy.power_consumption_15s)
        self.power_consumption_1m.notify_of_external_update(self.energy.power_consumption_1m)
        self.power_consumption_5m.notify_of_external_update(self.energy.power_consumption_5m)



