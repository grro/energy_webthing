from requests import Session
from abc import ABC, abstractmethod
import logging
from time import sleep
from typing import Tuple, List, Dict, Optional



class Shelly3PhaseMeter(ABC):

    @abstractmethod
    def query(self) -> Tuple[int, int, int, int]:
        pass



class Shelly3em(Shelly3PhaseMeter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> Tuple[int, int, int, int]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/EM.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    current_power = round(data['total_act_power'])
                    current_power_phase_a = round(data['a_act_power'])
                    current_power_phase_b = round(data['b_act_power'])
                    current_power_phase_c = round(data['c_act_power'])
                    return current_power, current_power_phase_a, current_power_phase_b, current_power_phase_c
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



class ShellyMeter(ABC):

    @abstractmethod
    def query(self) -> int:
        pass



class Shelly1pro(ShellyMeter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> int:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/switch.GetStatus?id=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return round(data['apower'])
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


class Shelly1pm(ShellyMeter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> int:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/status'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    return round(data['meters'][0]['power'])
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


class ShellyPmMini(ShellyMeter):

    def __init__(self, addr: str):
        self.__session = Session()
        self.addr = addr

    def query(self) -> Tuple[int, int, int, int]:
        ex = None
        for i in range(0,3):
            uri = self.addr + '/rpc/Shelly.GetStatus?channel=0'
            try:
                resp = self.__session.get(uri, timeout=20)
                try:
                    data = resp.json()
                    current_power = round(data['pm1:0']['apower'])
                    return current_power
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



class ShellyAutoMeter(ShellyMeter):

    def __init__(self, addr: str):
        self.meter = ShellyAutoMeter.auto_select(addr)

    @staticmethod
    def auto_select(addr: str):
        try:
            s = Shelly1pro(addr)
            s.query()
            logging.info("detected shelly1pro running on " + addr)
            return s
        except Exception as e:
            pass

        try:
            s = Shelly1pm(addr)
            s.query()
            logging.info("detected shelly1pm running on " + addr)
            return s
        except Exception as e:
            pass

        try:
            s = ShellyPmMini(addr)
            s.query()
            logging.info("detected shellyPmMini running on " + addr)
            return s
        except Exception as e:
            pass

        logging.warning("unsupported shelly running on " + addr)
        return None

    def query(self) -> int:
        return self.meter.query()

