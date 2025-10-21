from requests import Session
from abc import ABC, abstractmethod
import logging
from time import sleep
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Measure:
    total: int
    channel_a: Optional[int] = None
    channel_b: Optional[int] = None
    channel_c: Optional[int] = None


@dataclass(frozen=True)
class Info:
    name: str
    type: str

class Meter(ABC):

    @abstractmethod
    def info(self) -> Info:
        pass

    @abstractmethod
    def measure(self) -> Optional[Measure]:
        pass

    @property
    def name(self) -> str:
        return self.info().name

    @property
    def type(self) -> str:
        return self.info().type


class Shelly3em(Meter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def info(self) -> Info:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetDeviceInfo'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Info(data['name'], data['app'])
                except Exception as e:
                    ex =  Exception("ShellyPmMini called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("ShellyPmMini called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex


    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/EM.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Measure(round(data['total_act_power']), round(data['a_act_power']), round(data['b_act_power']), round(data['c_act_power']))
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



class Shelly1pro(Meter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def info(self) -> Info:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetDeviceInfo'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Info(data['name'], data['app'])
                except Exception as e:
                    ex =  Exception("ShellyPmMini called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("ShellyPmMini called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex

    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/switch.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    power = round(data['apower'])
                    return Measure(power, power)
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



class ShellyPmMini(Meter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def info(self) -> Info:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetDeviceInfo'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Info(data['name'], data['app'])
                except Exception as e:
                    ex =  Exception("ShellyPmMini called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("ShellyPmMini called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex

    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetStatus?channel=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    power = round(data['pm1:0']['apower'])
                    return Measure(power, power)
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



class Shelly1pm(Meter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def info(self) -> Info:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetDeviceInfo'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return Info(data['name'], data['app'])
                except Exception as e:
                    ex =  Exception("ShellyPmMini called " + uri + " got " + str(resp.status_code) + " " + resp.text + " " + str(e))
            except Exception as e:
                self.__renew_session()
                ex = Exception("ShellyPmMini called " + uri + " got " + str(e))
            sleep(1)
        if ex is not None:
            raise ex


    def measure(self) -> Optional[Measure]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/status'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    power = round(data['meters'][0]['power'])
                    return Measure(power, power)
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


class ShellyMeter(Meter):

    def __init__(self, addr: str):
        self.addr = addr
        self.device = ShellyMeter.auto_select(addr)

    def info(self) -> Info:
        if self.device is None:
            self.device = ShellyMeter.auto_select(self.addr)
        try:
            return self.device.info()
        except Exception as e:
            self.device = None
            raise e

    def measure(self) -> Optional[Measure]:
        if self.device is None:
            self.device = ShellyMeter.auto_select(self.addr)
        try:
            return self.device.measure()
        except Exception as e:
            self.device = None
            raise e

    @staticmethod
    def auto_select(addr: str) -> Optional[Meter]:
        try:
            s = Shelly3em(addr)
            info = s.info()
            if info.type == "Pro3EM":
                logging.info("detected " + info.name + " (" + info.type + ") running on " + addr)
                return s
        except Exception as e:
            pass

        try:
            s = ShellyPmMini(addr)
            info = s.info()
            if info.type.startswith('MiniPMG'):
                logging.info("detected " + info.name + " (" + info.type + ") running on " + addr)
                return s
        except Exception as e:
            pass

        try:
            s = Shelly1pro(addr)
            info = s.info()
            if info.type == 'Pro1PM':
                logging.info("detected " + info.name + " (" + info.type + ") running on " + addr)
                return s
        except Exception as e:
            pass

        try:
            s = Shelly1pm(addr)
            s.info()
            logging.info("detected shelly1pm running on " + addr)
            return s
        except Exception as e:
            pass

        try:
            s = ShellyPmMini(addr)
            s.info()
            logging.info("detected shellyPmMini running on " + addr)
            return s
        except Exception as e:
            pass

        logging.warning("unsupported shelly running on " + addr)
        return None



