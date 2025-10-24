import tornado.ioloop
import logging
from threading import Thread
from time import sleep
from webthing import (Property, Thing, Value)
from shelly import ShellyMeter
from utils import WattRecorder


class Module:

    def __init__(self, addr: str):
        self.__shelly = ShellyMeter(addr)
        self.name = self.__shelly.name
        self.power = 0
        self.__pv_power_smoothen_recorder = WattRecorder()

    @property
    def power_5s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def power_15s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def power_1m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=1)

    def measure(self) -> int:
        try:
            power = self.__shelly.measure().total
            self.power = power
            self.__pv_power_smoothen_recorder.put(power)
            return power
        except Exception as e:
            return 0


class Pv:

    def __init__(self, meter_addr_pv_channel1: str, meter_addr_pv_channel2: str, meter_addr_pv_channel3: str, meter_addr_pv_channel4: str):
        self.__is_running = True
        self.__listeners = set()
        self.__module1 = Module(meter_addr_pv_channel1)
        self.__module2 = Module(meter_addr_pv_channel2)
        self.__module3 = Module(meter_addr_pv_channel3)
        self.__module4 = Module(meter_addr_pv_channel4)

        self.power_downstream = 0
        self.__pv_power_smoothen_recorder = WattRecorder()


    def addd_listener(self,listener):
        self.__listeners.add(listener)

    @property
    def power_downstream_5s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=5)

    @property
    def power_downstream_15s(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(second_range=15)

    @property
    def power_downstream_1m(self) -> int:
        return self.__pv_power_smoothen_recorder.watt_per_hour(minute_range=1)

    @property
    def power_downstream_module1(self) -> int:
        return self.__module1.power

    @property
    def power_downstream_module1_5s(self) -> int:
        return self.__module1.power_5s

    @property
    def power_downstream_module1_15s(self) -> int:
        return self.__module1.power_15s

    @property
    def power_downstream_module1_1m(self) -> int:
        return self.__module1.power_1m

    @property
    def power_downstream_module2(self) -> int:
        return self.__module2.power

    @property
    def power_downstream_module2_5s(self) -> int:
        return self.__module2.power_5s

    @property
    def power_downstream_module2_15s(self) -> int:
        return self.__module2.power_15s

    @property
    def power_downstream_module2_1m(self) -> int:
        return self.__module2.power_1m

    @property
    def power_downstream_module3(self) -> int:
        return self.__module3.power

    @property
    def power_downstream_module3_5s(self) -> int:
        return self.__module3.power_5s

    @property
    def power_downstream_module3_15s(self) -> int:
        return self.__module3.power_15s

    @property
    def power_downstream_module3_1m(self) -> int:
        return self.__module3.power_1m

    @property
    def power_downstream_module4(self) -> int:
        return self.__module4.power

    @property
    def power_downstream_module4_5s(self) -> int:
        return self.__module4.power_5s

    @property
    def power_downstream_module4_15s(self) -> int:
        return self.__module4.power_15s

    @property
    def power_downstream_module4_1m(self) -> int:
        return self.__module4.power_1m

    def add_listener(self,listener):
        self.__listeners.add(listener)

    def start(self):
        Thread(target=self.__measure_loop, daemon=True).start()

    def stop(self):
        self.__is_running = False

    def __measure_loop(self):
        while self.__is_running:
            try:
                self.__measure()
                for listener in self.__listeners:
                    listener()
                sleep(1.03)
            except Exception as e:
                logging.warning("error occurred on refresh " + str(e))
                sleep(3)

    def __measure(self) -> bool:
        try:
            power1 = self.__module1.measure()
            power1 = 0 if power1 <0 else power1
            power2 = self.__module2.measure()
            power2 = 0 if power2 <0 else power2
            power3 = self.__module3.measure()
            power3 = 0 if power3 <0 else power3
            power4 = self.__module4.measure()
            power4 = 0 if power4 <0 else power4

            power = power1 + power2 + power3 + power4
            self.power_downstream = power
            self.__pv_power_smoothen_recorder.put(power)
            return True
        except Exception as e:
            return False





class PvThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, pv: Pv):
        Thing.__init__(
            self,
            'urn:dev:ops:pv',
            'PvSensor',
            ['MultiLevelSensor'],
            "pv"
        )
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.pv = pv
        self.pv.add_listener(self.on_value_changed)


        self.power_downstream = Value(pv.power_downstream)
        self.add_property(
            Property(self,
                     'power_downstream',
                     self.power_downstream,
                     metadata={
                         'title': 'power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the pv',
                         'readOnly': True,
                     }))

        self.power_downstream_5s = Value(pv.power_downstream_5s)
        self.add_property(
            Property(self,
                     'power_downstream_5s',
                     self.power_downstream_5s,
                     metadata={
                         'title': 'power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the pv  (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_15s = Value(pv.power_downstream_15s)
        self.add_property(
            Property(self,
                     'power_downstream_15s',
                     self.power_downstream_15s,
                     metadata={
                         'title': 'power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the pv  (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_1m = Value(pv.power_downstream_1m)
        self.add_property(
            Property(self,
                     'power_downstream_1m',
                     self.power_downstream_1m,
                     metadata={
                         'title': 'power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the pv  (smoothen 1 min)',
                         'readOnly': True,
                     }))


        self.power_downstream_module1 = Value(pv.power_downstream_module1)
        self.add_property(
            Property(self,
                     'module1__power_downstream',
                     self.power_downstream_module1,
                     metadata={
                         'title': 'module1 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module1',
                         'readOnly': True,
                     }))

        self.power_downstream_module1_5s = Value(pv.power_downstream_module1_5s)
        self.add_property(
            Property(self,
                     'module1_power_downstream_5s',
                     self.power_downstream_module1_5s,
                     metadata={
                         'title': 'module1 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 1 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1_15s = Value(pv.power_downstream_module1_15s)
        self.add_property(
            Property(self,
                     'module1_power_downstream_15s',
                     self.power_downstream_module1_15s,
                     metadata={
                         'title': 'module1 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 1 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1_1m = Value(pv.power_downstream_module1_1m)
        self.add_property(
            Property(self,
                     'module1_power_downstream_1m',
                     self.power_downstream_module1_1m,
                     metadata={
                         'title': 'module1 power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 1 (smoothen 1 min)',
                         'readOnly': True,
                     }))


        self.power_downstream_module2 = Value(pv.power_downstream_module2)
        self.add_property(
            Property(self,
                     'module2_power_downstream',
                     self.power_downstream_module2,
                     metadata={
                         'title': 'module2 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module2',
                         'readOnly': True,
                     }))

        self.power_downstream_module2_5s = Value(pv.power_downstream_module2_5s)
        self.add_property(
            Property(self,
                     'module2_power_downstream_5s',
                     self.power_downstream_module2_5s,
                     metadata={
                         'title': 'module1 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 2 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module2_15s = Value(pv.power_downstream_module2_15s)
        self.add_property(
            Property(self,
                     'module2_power_downstream_15s',
                     self.power_downstream_module2_15s,
                     metadata={
                         'title': 'module2 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 2 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module2_1m = Value(pv.power_downstream_module2_1m)
        self.add_property(
            Property(self,
                     'module2_power_downstream_1m',
                     self.power_downstream_module2_1m,
                     metadata={
                         'title': 'module2 power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 2 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module3 = Value(pv.power_downstream_module3)
        self.add_property(
            Property(self,
                     'module3_power_downstream',
                     self.power_downstream_module3,
                     metadata={
                         'title': 'module3 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module3',
                         'readOnly': True,
                     }))

        self.power_downstream_module3_5s = Value(pv.power_downstream_module3_5s)
        self.add_property(
            Property(self,
                     'module3_power_downstream_5s',
                     self.power_downstream_module3_5s,
                     metadata={
                         'title': 'module3 power dowstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 3 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module3_15s = Value(pv.power_downstream_module3_15s)
        self.add_property(
            Property(self,
                     'module3_power_downstream_15s',
                     self.power_downstream_module3_15s,
                     metadata={
                         'title': 'module3 power dwonstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 3 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module3_1m = Value(pv.power_downstream_module3_1m)
        self.add_property(
            Property(self,
                     'module3_power_downstream_1m',
                     self.power_downstream_module3_1m,
                     metadata={
                         'title': 'module3 power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 3 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module4 = Value(pv.power_downstream_module4)
        self.add_property(
            Property(self,
                     'module4_power_downstream',
                     self.power_downstream_module4,
                     metadata={
                         'title': 'module4 power downstream',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module4',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_5s = Value(pv.power_downstream_module4_5s)
        self.add_property(
            Property(self,
                     'module4_power_downstream_5s',
                     self.power_downstream_module4_5s,
                     metadata={
                         'title': 'module4 power downstream 5s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 5 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_15s = Value(pv.power_downstream_module4_15s)
        self.add_property(
            Property(self,
                     'module4_power_downstream_15s',
                     self.power_downstream_module4_15s,
                     metadata={
                         'title': 'module4 power downstream 15s',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 15 sec)',
                         'readOnly': True,
                     }))

        self.power_downstream_module4_1m = Value(pv.power_downstream_module4_1m)
        self.add_property(
            Property(self,
                     'module4_power_downstream_1m',
                     self.power_downstream_module4_1m,
                     metadata={
                         'title': 'module4 power downstream 1m',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the power of the module 4 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1u2_1m = Value(pv.power_downstream_module1_1m + pv.power_downstream_module2_1m)
        self.add_property(
            Property(self,
                     'module1u2_power_downstream_1m',
                     self.power_downstream_module1u2_1m,
                     metadata={
                         'title': 'module1 + module2 power downstream 1min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module1 + module2 (smoothen 1 min)',
                         'readOnly': True,
                     }))

        self.power_downstream_module1u2u3_1m = Value(pv.power_downstream_module1_1m + pv.power_downstream_module2_1m + pv.power_downstream_module3_1m )
        self.add_property(
            Property(self,
                     'module1u2u3_power_downstream_1m',
                     self.power_downstream_module1u2u3_1m,
                     metadata={
                         'title': 'module1 + module2 + module3 power downstream 1 min',
                         "type": "integer",
                         'unit': 'watt',
                         'description': 'the current power of the module1 + module2 + module3 (smoothen 1 min)',
                         'readOnly': True,
                     }))



    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.power_downstream.notify_of_external_update(self.pv.power_downstream)
        self.power_downstream_5s.notify_of_external_update(self.pv.power_downstream_5s)
        self.power_downstream_15s.notify_of_external_update(self.pv.power_downstream_15s)
        self.power_downstream_1m.notify_of_external_update(self.pv.power_downstream_1m)

        self.power_downstream_module1.notify_of_external_update(self.pv.power_downstream_module1)
        self.power_downstream_module1_5s.notify_of_external_update(self.pv.power_downstream_module1_5s)
        self.power_downstream_module1_15s.notify_of_external_update(self.pv.power_downstream_module1_15s)
        self.power_downstream_module1_1m.notify_of_external_update(self.pv.power_downstream_module1_1m)

        self.power_downstream_module2.notify_of_external_update(self.pv.power_downstream_module2)
        self.power_downstream_module2_5s.notify_of_external_update(self.pv.power_downstream_module2_5s)
        self.power_downstream_module2_15s.notify_of_external_update(self.pv.power_downstream_module2_15s)
        self.power_downstream_module2_1m.notify_of_external_update(self.pv.power_downstream_module2_1m)

        self.power_downstream_module3.notify_of_external_update(self.pv.power_downstream_module3)
        self.power_downstream_module3_5s.notify_of_external_update(self.pv.power_downstream_module3_5s)
        self.power_downstream_module3_15s.notify_of_external_update(self.pv.power_downstream_module3_15s)
        self.power_downstream_module3_1m.notify_of_external_update(self.pv.power_downstream_module3_1m)

        self.power_downstream_module4.notify_of_external_update(self.pv.power_downstream_module4)
        self.power_downstream_module4_5s.notify_of_external_update(self.pv.power_downstream_module4_5s)
        self.power_downstream_module4_15s.notify_of_external_update(self.pv.power_downstream_module4_15s)
        self.power_downstream_module4_1m.notify_of_external_update(self.pv.power_downstream_module4_1m)

        self.power_downstream_module1u2_1m.notify_of_external_update(self.pv.power_downstream_module1_1m + self.pv.power_downstream_module2_1m)
        self.power_downstream_module1u2u3_1m.notify_of_external_update(self.pv.power_downstream_module1_1m + self.pv.power_downstream_module2_1m + self.pv.power_downstream_module3_1m)