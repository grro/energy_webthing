import tornado.ioloop
import logging
from threading import Thread
from time import sleep
from webthing import (Property, Thing, Value)



class Battery:

    def __init__(self):
        self.__listeners = set()
        self.__is_running = True

    def add_listener(self,listener):
        self.__listeners.add(listener)

    @property
    def power_upstream(self) -> int:
        return 0

    @property
    def power_upstream_5s(self) -> int:
        return 0

    @property
    def power_upstream_15s(self) -> int:
        return 0

    @property
    def power_downstream(self) -> int:
        return 0

    @property
    def power_downstream_5s(self) -> int:
        return 0

    @property
    def power_downstream_15s(self) -> int:

        return 0

    def __on_update(self):
        for listener in self.__listeners:
            listener()

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __measure_loop(self):
        while self.__is_running:
            try:
                #self.__measure()
                for listener in self.__listeners:
                    listener()
                sleep(1.03)
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
                sleep(3)


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



    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.power_upstream.notify_of_external_update(self.battery.power_upstream)
        self.power_upstream_5s.notify_of_external_update(self.battery.power_upstream_5s)
        self.power_upstream_15s.notify_of_external_update(self.battery.power_upstream_15s)
        self.power_downstream.notify_of_external_update(self.battery.power_downstream)
        self.power_downstream_5s.notify_of_external_update(self.battery.power_downstream_5s)
        self.power_downstream_15s.notify_of_external_update(self.battery.power_downstream_15s)


