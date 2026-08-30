from requests import Session
import logging


class Heater:

    def __init__(self, addr: str):
        self.addr = addr
        self.__session = Session()
        self.__data: dict = {}

    def fetch(self):
        for i in range(3):
            try:
                resp = self.__session.get(self.addr, timeout=20)
                resp.raise_for_status()
                self.__data = resp.json()
                return
            except Exception as e:
                logging.warning("Heater called " + self.addr + " got " + str(e))
                self.__renew_session(str(e))
        logging.warning("Heater fetch failed after retries")

    def __renew_session(self, reason: str = ""):
        logging.info("Heater renew session for " + self.addr + (" reason: " + reason if reason else ""))
        try:
            self.__session.close()
        except Exception as e:
            logging.warning(str(e))
        self.__session = Session()

    @property
    def power(self) -> int:
        self.fetch()
        return self.__data.get("power", 0)

