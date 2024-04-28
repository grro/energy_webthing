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
            'Energy Sensor',
            ['MultiLevelSensor'],
            description
        )
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.energy = energy
        self.energy.set_listener(self.on_value_changed)

        self.current_power_consumption = Value(energy.current_power_consumption)
        self.add_property(
            Property(self,
                     'current_power_consumption',
                     self.current_power_consumption,
                     metadata={
                         'title': 'current_power_consumption',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed',
                         'readOnly': True,
                     }))

        self.current_power_consumption_smoothen_1m = Value(energy.current_power_consumption_smoothen_1m)
        self.add_property(
            Property(self,
                     'current_power_consumption_smoothen_1m',
                     self.current_power_consumption_smoothen_1m,
                     metadata={
                         'title': 'current_power_consumption_smoothen_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.current_power_consumption_smoothen_3m = Value(energy.current_power_consumption_smoothen_3m)
        self.add_property(
            Property(self,
                     'current_power_consumption_smoothen_3m',
                     self.current_power_consumption_smoothen_3m,
                     metadata={
                         'title': 'current_power_consumption_smoothen_3m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed (smoothen 3 min)',
                         'readOnly': True,
                     }))

        self.current_power_provider = Value(energy.current_power_provider)
        self.add_property(
            Property(self,
                     'current_power_provider',
                     self.current_power_provider,
                     metadata={
                         'title': 'current_power_provider',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the provider (may be negative)',
                         'readOnly': True,
                     }))

        self.current_power_pv = Value(energy.current_power_pv)
        self.add_property(
            Property(self,
                     'current_power_pv',
                     self.current_power_pv,
                     metadata={
                         'title': 'current_power_pv',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced',
                         'readOnly': True,
                     }))

        self.current_power_pv_smoothen_1m = Value(energy.current_power_pv_smoothen_1m)
        self.add_property(
            Property(self,
                     'current_power_pv_smoothen_1m',
                     self.current_power_pv_smoothen_1m,
                     metadata={
                         'title': 'current_power_pv_smoothen_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced (smoothen 1 min)',
                         'readOnly': True,
                     }))


        self.current_power_pv_smoothen_3m = Value(energy.current_power_pv_smoothen_3m)
        self.add_property(
            Property(self,
                     'current_power_pv_smoothen_3m',
                     self.current_power_pv_smoothen_3m,
                     metadata={
                         'title': 'current_power_pv_smoothen_3m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced (smoothen 3 min)',
                         'readOnly': True,
                     }))

        self.current_power_pv_surplus = Value(energy.current_power_pv_surplus)
        self.add_property(
            Property(self,
                     'current_power_pv_surplus',
                     self.current_power_pv_surplus,
                     metadata={
                         'title': 'current_power_pv_surplus',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed',
                         'readOnly': True,
                     }))


        self.current_power_pv_surplus_smoothen_5s = Value(energy.current_power_pv_surplus_smoothen_5s)
        self.add_property(
            Property(self,
                     'current_power_pv_surplus_smoothen_5s',
                     self.current_power_pv_surplus_smoothen_5s,
                     metadata={
                         'title': 'current_power_pv_surplus_smoothen_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.current_power_pv_surplus_smoothen_1m = Value(energy.current_power_pv_surplus_smoothen_1m)
        self.add_property(
            Property(self,
                     'current_power_pv_surplus_smoothen_1m',
                     self.current_power_pv_surplus_smoothen_1m,
                     metadata={
                         'title': 'current_power_pv_surplus_smoothen_1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.current_power_pv_surplus_smoothen_3m = Value(energy.current_power_pv_surplus_smoothen_3m)
        self.add_property(
            Property(self,
                     'current_power_pv_surplus_smoothen_3m',
                     self.current_power_pv_surplus_smoothen_3m,
                     metadata={
                         'title': 'current_power_pv_surplus_smoothen_3m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 3 min)',
                         'readOnly': True,
                     }))

        self.current_power_pv_surplus_smoothen_5m = Value(energy.current_power_pv_surplus_smoothen_5m)
        self.add_property(
            Property(self,
                     'current_power_pv_surplus_smoothen_5m',
                     self.current_power_pv_surplus_smoothen_5m,
                     metadata={
                         'title': 'current_power_pv_surplus_smoothen_5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 5 min)',
                         'readOnly': True,
                     }))



    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.current_power_provider.notify_of_external_update(self.energy.current_power_provider)

        self.current_power_consumption.notify_of_external_update(self.energy.current_power_consumption)
        self.current_power_consumption_smoothen_1m.notify_of_external_update(self.energy.current_power_consumption_smoothen_1m)
        self.current_power_consumption_smoothen_3m.notify_of_external_update(self.energy.current_power_consumption_smoothen_3m)

        self.current_power_pv.notify_of_external_update(self.energy.current_power_pv)
        self.current_power_pv_smoothen_1m.notify_of_external_update(self.energy.current_power_pv_smoothen_1m)
        self.current_power_pv_smoothen_3m.notify_of_external_update(self.energy.current_power_pv_smoothen_3m)

        self.current_power_pv_surplus.notify_of_external_update(self.energy.current_power_pv_surplus)
        self.current_power_pv_surplus_smoothen_5s.notify_of_external_update(self.energy.current_power_pv_surplus_smoothen_5s)
        self.current_power_pv_surplus_smoothen_1m.notify_of_external_update(self.energy.current_power_pv_surplus_smoothen_1m)
        self.current_power_pv_surplus_smoothen_3m.notify_of_external_update(self.energy.current_power_pv_surplus_smoothen_3m)
        self.current_power_pv_surplus_smoothen_5m.notify_of_external_update(self.energy.current_power_pv_surplus_smoothen_5m)


def run_server(description: str, port: int, meter_addr_provider: str, meter_addr_pv: str):
    energy = Energy(meter_addr_provider, meter_addr_pv)
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
    run_server("description", int(sys.argv[1]), sys.argv[2], sys.argv[3])
