import sys
import logging
import tornado.ioloop
from webthing import (SingleThing, Property, Thing, Value, WebThingServer)
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

        self.pv_measures_updated = Value(energy.pv_measures_updated.strftime("%Y-%m-%dT%H:%M:%S+00:00"))
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

        self.provider_measures_updated_utc = Value(energy.provider_measures_updated_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00"))
        self.add_property(
            Property(self,
                     'provider_measures_updated_utc',
                     self.provider_measures_updated_utc,
                     metadata={
                         'title': 'provider_measures_updated_utc',
                         "type": "string",
                         'unit': 'ISO8601 datetime',
                         'description': 'the datetime when the provider values has been updated',
                         'readOnly': True,
                     }))

        self.provider_power = Value(energy.provider_power)
        self.add_property(
            Property(self,
                     'provider',
                     self.provider_power,
                     metadata={
                         'title': 'provider',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the provider (may be negative)',
                         'readOnly': True,
                     }))

        self.pv_power = Value(energy.pv_power)
        self.add_property(
            Property(self,
                     'pv',
                     self.pv_power,
                     metadata={
                         'title': 'pv',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced',
                         'readOnly': True,
                     }))

        self.pv_power_channel_1 = Value(energy.pv_power_channel_1)
        self.add_property(
            Property(self,
                     'pv_channel1',
                     self.pv_power_channel_1,
                     metadata={
                         'title': 'pv_channel1',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power channel 1 produced',
                         'readOnly': True,
                     }))

        self.pv_power_channel_2 = Value(energy.pv_power_channel_2)
        self.add_property(
            Property(self,
                     'pv_channel2',
                     self.pv_power_channel_2,
                     metadata={
                         'title': 'pv_channel2',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power channel 2 produced',
                         'readOnly': True,
                     }))

        self.pv_power_channel_3 = Value(energy.pv_power_channel_3)
        self.add_property(
            Property(self,
                     'pv_channel3',
                     self.pv_power_channel_3,
                     metadata={
                         'title': 'pv_channel3',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power channel 3 produced',
                         'readOnly': True,
                     }))

        self.pv_power_channel_1u2 = Value(energy.pv_power_channel_1 + energy.pv_power_channel_2)
        self.add_property(
            Property(self,
                     'pv_channel1u2',
                     self.pv_power_channel_1u2,
                     metadata={
                         'title': 'pv_channel 1 & 2',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power channel 1 & 2 produced',
                         'readOnly': True,
                     }))

        self.pv_power_channel_1u2u3 = Value(energy.pv_power_channel_1 + energy.pv_power_channel_2 + energy.pv_power_channel_3)
        self.add_property(
            Property(self,
                     'pv_channel1u2u3',
                     self.pv_power_channel_1u2u3,
                     metadata={
                         'title': 'pv_channel 1 & 2 & 3',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power channel 1 & 2 & 3 produced',
                         'readOnly': True,
                     }))

        self.pv_effective_power = Value(energy.pv_effective_power)
        self.add_property(
            Property(self,
                     'pv_effective',
                     self.pv_effective_power,
                     metadata={
                         'title': 'pv_effective',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current effective pv power',
                         'readOnly': True,
                     }))

        self.consumption_power = Value(energy.consumption_power)
        self.add_property(
            Property(self,
                     'consumption',
                     self.consumption_power,
                     metadata={
                         'title': 'consumption',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed',
                         'readOnly': True,
                     }))



        self.pv_surplus_power = Value(energy.pv_surplus_power)
        self.add_property(
            Property(self,
                     'pv_surplus',
                     self.pv_surplus_power,
                     metadata={
                         'title': 'pv_surplus',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed',
                         'readOnly': True,
                     }))

        self.consumption_power_estimated_year = Value(energy.consumption_power_estimated_year)
        self.add_property(
            Property(self,
                     'consumption_estimated_year',
                     self.consumption_power_estimated_year,
                     metadata={
                         'title': 'consumption_estimated_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the estimated power consumption year',
                         'readOnly': True,
                     }))

        self.pv_power_estimated_year = Value(energy.pv_power_estimated_year)
        self.add_property(
            Property(self,
                     'pv_estimated_year',
                     self.pv_power_estimated_year,
                     metadata={
                         'title': 'pv_estimated_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the estimated pv power current year',
                         'readOnly': True,
                     }))

        self.pv_effective_power_estimated_year = Value(energy.pv_effective_power_estimated_year)
        self.add_property(
            Property(self,
                     'pv_effective_estimated_year',
                     self.pv_effective_power_estimated_year,
                     metadata={
                         'title': 'pv_effective_estimated_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the estimated effective pv power current year',
                         'readOnly': True,
                     }))

        self.pv_effective_power_estimated_year = Value(energy.pv_effective_power_estimated_year)
        self.add_property(
            Property(self,
                     'pv_effective_estimated_year',
                     self.pv_effective_power_estimated_year,
                     metadata={
                         'title': 'pv_effective_estimated_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the estimated effective pv power current year',
                         'readOnly': True,
                     }))

        self.pv_peek_hour_utc = Value(energy.pv_peek_hour_utc)
        self.add_property(
            Property(self,
                     'pv_peek_hour_utc',
                     self.pv_peek_hour_utc,
                     metadata={
                         'title': 'pv_peek_hour_utc',
                         "type": "integer",
                         'unit': 'hour',
                         'description': 'the peek pv hour (UTC)',
                         'readOnly': True,
                     }))

        self.provider_power_estimated_year = Value(energy.provider_power_estimated_year)
        self.add_property(
            Property(self,
                     'provider_power_estimated_year',
                     self.provider_power_estimated_year,
                     metadata={
                         'title': 'provider_power_estimated_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the estimated provider power current year',
                         'readOnly': True,
                     }))

        self.provider_power_5s = Value(energy.provider_power_5s)
        self.add_property(
            Property(self,
                     'provider_5s',
                     self.provider_power_5s,
                     metadata={
                         'title': 'provider_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.provider_power_current_hour = Value(energy.provider_power_current_hour)
        self.add_property(
            Property(self,
                     'provider_current_hour',
                     self.provider_power_current_hour,
                     metadata={
                         'title': 'provider_current_hour',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider  (current hour)',
                         'readOnly': True,
                     }))

        self.provider_power_current_day = Value(energy.provider_power_current_day)
        self.add_property(
            Property(self,
                     'provider_current_day',
                     self.provider_power_current_day,
                     metadata={
                         'title': 'provider_current_day',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider current day',
                         'readOnly': True,
                     }))

        self.provider_power_current_year = Value(energy.provider_power_current_year)
        self.add_property(
            Property(self,
                     'provider_current_year',
                     self.provider_power_current_year,
                     metadata={
                         'title': 'provider_current_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power provider current day',
                         'readOnly': True,
                     }))

        self.pv_power_5s = Value(energy.pv_power_5s)
        self.add_property(
            Property(self,
                     'pv_5s',
                     self.pv_power_5s,
                     metadata={
                         'title': 'pv_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.pv_power_current_hour = Value(energy.pv_power_current_hour)
        self.add_property(
            Property(self,
                     'pv_current_hour',
                     self.pv_power_current_hour,
                     metadata={
                         'title': 'pv_current_hour',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power produced (current hour)',
                         'readOnly': True,
                     }))

        self.pv_power_current_day = Value(energy.pv_power_current_day)
        self.add_property(
            Property(self,
                     'pv_current_day',
                     self.pv_power_current_day,
                     metadata={
                         'title': 'pv_current_day',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the pv power current day',
                         'readOnly': True,
                     }))

        self.pv_power_current_year = Value(energy.pv_power_current_year)
        self.add_property(
            Property(self,
                     'pv_current_year',
                     self.pv_power_current_year,
                     metadata={
                         'title': 'pv_current_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the pv power current year',
                         'readOnly': True,
                     }))

        self.consumption_power_5s = Value(energy.consumption_power_5s)
        self.add_property(
            Property(self,
                     'consumption_5s',
                     self.consumption_power_5s,
                     metadata={
                         'title': 'consumption_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.consumption_power_current_hour = Value(energy.consumption_power_current_hour)
        self.add_property(
            Property(self,
                     'consumption_current_hour',
                     self.consumption_power_current_hour,
                     metadata={
                         'title': 'consumption_current_hour',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power currently consumed (current hour)',
                         'readOnly': True,
                     }))

        self.consumption_power_current_day = Value(energy.consumption_power_current_day)
        self.add_property(
            Property(self,
                     'consumption_current_day',
                     self.consumption_power_current_day,
                     metadata={
                         'title': 'consumption_current_day',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the consumption provider current day',
                         'readOnly': True,
                     }))

        self.consumption_power_current_year = Value(energy.consumption_power_current_year)
        self.add_property(
            Property(self,
                     'consumption_power_current_year',
                     self.consumption_power_current_year,
                     metadata={
                         'title': 'consumption_power_current_year',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the consumption provider current year',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_5s = Value(energy.pv_surplus_power_5s)
        self.add_property(
            Property(self,
                     'pv_surplus_5s',
                     self.pv_surplus_power_5s,
                     metadata={
                         'title': 'pv_surplus_5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_15s = Value(energy.pv_surplus_power_15s)
        self.add_property(
            Property(self,
                     'pv_surplus_15s',
                     self.pv_surplus_power_15s,
                     metadata={
                         'title': 'pv_surplus_15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_5m = Value(energy.pv_surplus_power_5m)
        self.add_property(
            Property(self,
                     'pv_surplus_5m',
                     self.pv_surplus_power_5m,
                     metadata={
                         'title': 'pv_surplus_5m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (smoothen 5 min)',
                         'readOnly': True,
                     }))

        self.pv_surplus_power_current_hour = Value(energy.pv_surplus_power_current_hour)
        self.add_property(
            Property(self,
                     'pv_surplus_current_hour',
                     self.pv_surplus_power_current_hour,
                     metadata={
                         'title': 'pv_surplus_current_hour',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current pv power not consumed (current hour)',
                         'readOnly': True,
                     }))

    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.provider_measures_updated_utc.notify_of_external_update(self.energy.provider_measures_updated_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00"))
        self.provider_power.notify_of_external_update(self.energy.provider_power)
        self.provider_power_estimated_year.notify_of_external_update(self.energy.provider_power_estimated_year)
        self.provider_power_5s.notify_of_external_update(self.energy.provider_power_5s)
        self.provider_power_current_hour.notify_of_external_update(self.energy.provider_power_current_hour)
        self.provider_power_current_day.notify_of_external_update(self.energy.provider_power_current_day)
        self.provider_power_current_year.notify_of_external_update(self.energy.provider_power_current_year)

        self.consumption_power.notify_of_external_update(self.energy.consumption_power)
        self.consumption_power_5s.notify_of_external_update(self.energy.consumption_power_5s)
        self.consumption_power_current_hour.notify_of_external_update(self.energy.consumption_power_current_hour)
        self.consumption_power_current_day.notify_of_external_update(self.energy.consumption_power_current_day)
        self.consumption_power_current_year.notify_of_external_update(self.energy.consumption_power_current_year)
        self.consumption_power_estimated_year.notify_of_external_update(self.energy.consumption_power_estimated_year)

        self.pv_measures_updated.notify_of_external_update(self.energy.pv_measures_updated.strftime("%Y-%m-%dT%H:%M:%S+00:00"))
        self.pv_power.notify_of_external_update(self.energy.pv_power)
        self.pv_power_channel_1.notify_of_external_update(self.energy.pv_power_channel_1)
        self.pv_power_channel_2.notify_of_external_update(self.energy.pv_power_channel_2)
        self.pv_power_channel_3.notify_of_external_update(self.energy.pv_power_channel_3)
        self.pv_power_channel_1u2.notify_of_external_update(self.energy.pv_power_channel_1 + self.energy.pv_power_channel_2)
        self.pv_power_channel_1u2u3.notify_of_external_update(self.energy.pv_power_channel_1 + self.energy.pv_power_channel_2 + self.energy.pv_power_channel_3)
        self.pv_power_5s.notify_of_external_update(self.energy.pv_power_5s)
        self.pv_power_current_hour.notify_of_external_update(self.energy.pv_power_current_hour)
        self.pv_power_current_day.notify_of_external_update(self.energy.pv_power_current_day)
        self.pv_power_current_year.notify_of_external_update(self.energy.pv_power_current_year)
        self.pv_power_estimated_year.notify_of_external_update(self.energy.pv_power_estimated_year)
        self.pv_effective_power.notify_of_external_update(self.energy.pv_effective_power)
        self.pv_effective_power_estimated_year.notify_of_external_update(self.energy.pv_effective_power_estimated_year)
        self.pv_peek_hour_utc.notify_of_external_update(self.energy.pv_peek_hour_utc)

        self.pv_surplus_power.notify_of_external_update(self.energy.pv_surplus_power)
        self.pv_surplus_power_5s.notify_of_external_update(self.energy.pv_surplus_power_5s)
        self.pv_surplus_power_15s.notify_of_external_update(self.energy.pv_surplus_power_15s)
        self.pv_surplus_power_5m.notify_of_external_update(self.energy.pv_surplus_power_5m)
        self.pv_surplus_power_current_hour.notify_of_external_update(self.energy.pv_surplus_power_current_hour)

def run_server(description: str,
               port: int,
               meter_addr_provider: str,
               meter_addr_pv: str,
               meter_addr_pv_channel1: str,
               meter_addr_pv_channel2: str,
               meter_addr_pv_channel3: str,
               directory: str,
               min_pv_power : int):
    energy = Energy(meter_addr_provider, meter_addr_pv, meter_addr_pv_channel1, meter_addr_pv_channel2, meter_addr_pv_channel3, directory, min_pv_power)
    server = WebThingServer(SingleThing(EnergyThing(description, energy)), port=port, disable_host_validation=True)
    try:
        logging.info('starting the server http://localhost:' + str(port) + " (provider meter=" + meter_addr_provider + "; pv meter=" + meter_addr_pv + "; min pv power="  + str(min_pv_power) + ")")
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
    run_server("description", int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], int(sys.argv[8]))
