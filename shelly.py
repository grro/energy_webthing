from requests import Session
from abc import ABC, abstractmethod
import logging
from time import sleep
from typing import Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Measure:
    power: int


@dataclass(frozen=True)
class ThreePhaseMeasure(Measure):
    a_power: int
    b_power: int
    c_power: int





class Device(ABC):

    @abstractmethod
    def measure(self) -> Optional[Measure]:
        pass


class Shelly3em(Device):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/EM.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return ThreePhaseMeasure(round(data['total_act_power']), round(data['a_act_power']), round(data['b_act_power']), round(data['c_act_power']))
                except Exception as e:
                    ex = Exception("Shelly3em called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("Shelly3em called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex

    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()



class Shelly1pro(Device):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/switch.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Measure(round(data['apower']))
                except Exception as e:
                    ex = Exception("Shelly1pro called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("Shelly1pro called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex

    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()



class ShellyPmMini(Device):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetStatus?channel=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Measure(round(data['pm1:0']['apower']))
                except Exception as e:
                    ex =  Exception("ShellyPmMini called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("ShellyPmMini called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex

    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()



class Shelly1pm(Device):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/status'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Measure(round(data['meters'][0]['power']))
                except Exception as e:
                    ex = Exception("Shelly1pm called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("Shelly1pm called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex


    def __renew_session(self):
        logging.info("renew session for " + self.addr)
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()


class ShellyMeter(Device):

    def __init__(self, addr: str):
        self.device = ShellyMeter.auto_select(addr)

    def measure(self) -> Optional[Measure]:
        return self.device.measure()

    @staticmethod
    def auto_select(addr: str) -> Device:
        try:
            s = Shelly1pro(addr)
            s.measure()
            logging.info("detected shelly1pro running on " + addr)
            return s
        except Exception as e:
            pass

        try:
            s = Shelly1pm(addr)
            s.measure()
            logging.info("detected shelly1pm running on " + addr)
            return s
        except Exception as e:
            pass

        try:
            s = ShellyPmMini(addr)
            s.measure()
            logging.info("detected shellyPmMini running on " + addr)
            return s
        except Exception as e:
            pass

        try:
            s = Shelly3em(addr)
            s.measure()
            logging.info("detected shelly3em running on " + addr)
            return s
        except Exception as e:
            pass

        logging.warning("unsupported shelly running on " + addr)
        return None



