from webthing import (SingleThing, Property, Thing, Value, WebThingServer)
import sys
import logging
import tornado.ioloop
from energy import Energy




class EnergyThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, description: str, energy: Energy):
        Thing.__init__(
            self,
            'urn:dev:ops:energy-1',
            'EnergySensor',
            ['MultiLevelSensor'],
            description
        )
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.energy = energy
        self.energy.set_listener(self.on_value_changed)

        self.pv_measures_updated = Value(energy.pv_measures_updated.strftime("%Y-%m-%dT%H:%M:%S"))
        self.add_property(
            Property(self,
                     'pv_measures_updated',
                     self.pv_measures_updated,
                     metadata={
                         'title': 'pv_measures_updated',
                         "type": "string",
                         'unit': 'ISO8601 datetime',
                         'description': 'the datetime when the pv values has been updated',
                         'readOnly': True,
                     }))

        self.provider_measures_updated = Value(energy.provider_measures_updated.strftime("%Y-%m-%dT%H:%M:%S"))
        self.add_property(
            Property(self,
                     'provider_measures_updated',
                     self.provider_measures_updated,
                     metadata={
                         'title': 'provider_measures_updated',
                         "type": "string",
                         'unit': 'ISO8601 datetime',
                         'description': 'the datetime when the provider values has been updated',
                         'readOnly': True,
                     }))


        self.provider_power = Value(energy.provider_power)
        self.add_property(
            Property(self,
                     'provider_power',
                     self.provider_power,
                     metadata={
                         'title': 'provider_power',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the provider (may be negative)',
                         'readOnly': True,
                     }))

        self.provider_power_1m = Value(energy.provider_power_1m)
        self.add_property(
            Property(self,
                     'provider_power_1m',
                     self.provider_power_1m,
                     metadata={
                         'title': 'provider_power_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.provider_power_3m = Value(energy.provider_power_3m)
        self.add_property(
            Property(self,
                     'provider_power_3m',
                     self.provider_power_3m,
                     metadata={
                         'title': 'provider_power_3m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 3 min)',
                         'readOnly': True,
                     }))


        self.provider_power_60m = Value(energy.provider_power_60m)
        self.add_property(
            Property(self,
                     'provider_power_60m',
                     self.provider_power_60m,
                     metadata={
                         'title': 'provider_power_60m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 60 min)',
                         'readOnly': True,
                     }))

        self.provider_power_current_day = Value(energy.provider_power_current_day)
        self.add_property(
            Property(self,
                     'provider_power_current_day',
                     self.provider_power_current_day,
                     metadata={
                         'title': 'provider_power_current_day',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider current day',
                         'readOnly': True,
                     }))

        self.pv_power = Value(energy.pv_power)
        self.add_property(
            Property(self,
                     'pv_power',
                     self.pv_power,
                     metadata={
                         'title': 'pv_power',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced',
                         'readOnly': True,
                     }))

        self.pv_power_1m = Value(energy.pv_power_1m)
        self.add_property(
            Property(self,
                     'pv_power_1m',
                     self.pv_power_1m,
                     metadata={
                         'title': 'pv_power_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced (smoothen 1 min)',
                         'readOnly': True,
                     }))


        self.pv_power_3m = Value(energy.pv_power_3m)
        self.add_property(
            Property(self,
                     'pv_power_3m',
                     self.pv_power_3m,
                     metadata={
                         'title': 'pv_power_3m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced (smoothen 3 min)',
                         'readOnly': True,
                     }))

        self.pv_power_60m = Value(energy.pv_power_60m)
        self.add_property(
            Property(self,
                     'pv_power_60m',
                     self.pv_power_60m,
                     metadata={
                         'title': 'pv_power_60m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced (smoothen 60 min)',
                         'readOnly': True,
                     }))

        self.pv_power_current_day = Value(energy.pv_power_current_day)
        self.add_property(
            Property(self,
                     'pv_power_current_day',
                     self.pv_power_current_day,
                     metadata={
                         'title': 'pv_power_current_day',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the pv power current day',
                         'readOnly': True,
                     }))

        self.consumption_power = Value(energy.consumption_power)
        self.add_property(
            Property(self,
                     'consumption_power',
                     self.consumption_power,
                     metadata={
                         'title': 'consumption_power',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed',
                         'readOnly': True,
                     }))

        self.consumption_power_1m = Value(energy.consumption_power_1m)
        self.add_property(
            Property(self,
                     'consumption_power_1m',
                     self.consumption_power_1m,
                     metadata={
                         'title': 'consumption_power_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.consumption_power_3m = Value(energy.consumption_power_3m)
        self.add_property(
            Property(self,
                     'consumption_power_3m',
                     self.consumption_power_3m,
                     metadata={
                         'title': 'consumption_power_3m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed (smoothen 3 min)',
                         'readOnly': True,
                     }))

        self.consumption_power_60m = Value(energy.consumption_power_60m)
        self.add_property(
            Property(self,
                     'consumption_power_60m',
                     self.consumption_power_60m,
                     metadata={
                         'title': 'consumption_power_60m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed (smoothen 60 min)',
                         'readOnly': True,
                     }))



        self.consumption_power_current_day = Value(energy.consumption_power_current_day)
        self.add_property(
            Property(self,
                     'consumption_power_current_day',
                     self.consumption_power_current_day,
                     metadata={
                         'title': 'consumption_power_current_day',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the consumption provider current day',
                         'readOnly': True,
                     }))

        self.pv_surplus_power = Value(energy.pv_surplus_power)
        self.add_property(
            Property(self,
                     'pv_surplus_power',
                     self.pv_surplus_power,
                     metadata={
                         'title': 'pv_surplus_power',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed',
                         'readOnly': True,
                     }))


        self.pv_surplus_power_5s = Value(energy.pv_surplus_power_5s)
        self.add_property(
            Property(self,
                     'pv_surplus_power_5s',
                     self.pv_surplus_power_5s,
                     metadata={
                         'title': 'pv_surplus_power_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_1m = Value(energy.pv_surplus_power_1m)
        self.add_property(
            Property(self,
                     'pv_surplus_power_1m',
                     self.pv_surplus_power_1m,
                     metadata={
                         'title': 'pv_surplus_power_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_3m = Value(energy.pv_surplus_power_3m)
        self.add_property(
            Property(self,
                     'pv_surplus_power_3m',
                     self.pv_surplus_power_3m,
                     metadata={
                         'title': 'pv_surplus_power_3m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 3 min)',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_5m = Value(energy.pv_surplus_power_5m)
        self.add_property(
            Property(self,
                     'pv_surplus_power_5m',
                     self.pv_surplus_power_5m,
                     metadata={
                         'title': 'pv_surplus_power_5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_60m = Value(energy.pv_surplus_power_60m)
        self.add_property(
            Property(self,
                     'pv_surplus_power_60m',
                     self.pv_surplus_power_60m,
                     metadata={
                         'title': 'pv_surplus_power_60m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 60 min)',
                         'readOnly': True,
                     }))

        self.debug = Value(energy.debug)
        self.add_property(
            Property(self,
                     'debug',
                     self.debug,
                     metadata={
                         'title': 'debug',
                         'description': 'debug',
                         'readOnly': True,
                     }))

    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.provider_measures_updated.notify_of_external_update(self.energy.provider_measures_updated.strftime("%Y-%m-%dT%H:%M:%S"))
        self.provider_power.notify_of_external_update(self.energy.provider_power)
        self.provider_power_1m.notify_of_external_update(self.energy.provider_power_1m)
        self.provider_power_3m.notify_of_external_update(self.energy.provider_power_3m)
        self.provider_power_60m.notify_of_external_update(self.energy.provider_power_60m)
        self.provider_power_current_day.notify_of_external_update(self.energy.provider_power_current_day)

        self.consumption_power.notify_of_external_update(self.energy.consumption_power)
        self.consumption_power_1m.notify_of_external_update(self.energy.consumption_power_1m)
        self.consumption_power_3m.notify_of_external_update(self.energy.consumption_power_3m)
        self.consumption_power_60m.notify_of_external_update(self.energy.consumption_power_60m)
        self.consumption_power_current_day.notify_of_external_update(self.energy.consumption_power_current_day)

        self.pv_measures_updated.notify_of_external_update(self.energy.pv_measures_updated.strftime("%Y-%m-%dT%H:%M:%S"))
        self.pv_power.notify_of_external_update(self.energy.pv_power)
        self.pv_power_1m.notify_of_external_update(self.energy.pv_power_1m)
        self.pv_power_3m.notify_of_external_update(self.energy.pv_power_3m)
        self.pv_power_60m.notify_of_external_update(self.energy.pv_power_60m)
        self.pv_power_current_day.notify_of_external_update(self.energy.pv_power_current_day)

        self.pv_surplus_power.notify_of_external_update(self.energy.pv_surplus_power)
        self.pv_surplus_power_5s.notify_of_external_update(self.energy.pv_surplus_power_5s)
        self.pv_surplus_power_1m.notify_of_external_update(self.energy.pv_surplus_power_1m)
        self.pv_surplus_power_3m.notify_of_external_update(self.energy.pv_surplus_power_3m)
        self.pv_surplus_power_5m.notify_of_external_update(self.energy.pv_surplus_power_5m)
        self.pv_surplus_power_60m.notify_of_external_update(self.energy.pv_surplus_power_60m)

        self.debug.notify_of_external_update(self.energy.debug)


def run_server(description: str, port: int, meter_addr_provider: str, meter_addr_pv: str, directory: str):
    energy = Energy(meter_addr_provider, meter_addr_pv, directory)
    server = WebThingServer(SingleThing(EnergyThing(description, energy)), port=port, disable_host_validation=True)
    try:
        logging.info('starting the server http://localhost:' + str(port) + " (provider meter=" + meter_addr_provider + "; pv meter=" + meter_addr_pv + ")")
        energy.start()
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping the server')
        energy.stop()
        server.stop()
        logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(name)-20s: %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger('tornado.access').setLevel(logging.ERROR)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    run_server("description", int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
