import tornado.ioloop
from webthing import (Property, Thing, Value)
from energy import Energy


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

        self.power_green_1m = Value(energy.power_green_1m)
        self.add_property(
            Property(self,
                     'power_green_1m',
                     self.power_green_1m,
                     metadata={
                         'title': 'green power 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the green power (pv + battery) smoothen over 1 minute',
                         'readOnly': True,
                     }))

        self.power_core_consumption_5s = Value(energy.power_core_consumption_5s)
        self.add_property(
            Property(self,
                     'power_core_consumption_5s',
                     self.power_core_consumption_5s,
                     metadata={
                         'title': 'power core consumption 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power consumption without upstream provider + battery smoothen over 5 seconds',
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
        self.power_green_1m.notify_of_external_update(self.energy.power_green_1m)

        self.power_consumption.notify_of_external_update(self.energy.power_consumption)
        self.power_consumption_5s.notify_of_external_update(self.energy.power_consumption_5s)
        self.power_consumption_15s.notify_of_external_update(self.energy.power_consumption_15s)
        self.power_consumption_1m.notify_of_external_update(self.energy.power_consumption_1m)
        self.power_consumption_5m.notify_of_external_update(self.energy.power_consumption_5m)

        self.power_core_consumption_5s.notify_of_external_update(self.energy.power_core_consumption_5s)


