import tornado.ioloop
from webthing import (Property, Thing, Value)
from battery import Battery



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



