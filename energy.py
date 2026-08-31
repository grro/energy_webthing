from provider import Provider
from pv import Pv
from battery import Battery
from heater import Heater



class Energy:

    def __init__(self, provider: Provider, pv: Pv, battery: Battery, heater: Heater):
        self.__is_running = True
        self.__listeners = set()
        self.provider = provider
        self.pv = pv
        self.battery = battery
        self.heater = heater
        self.provider.add_listener(self.__on_update)
        self.pv.add_listener(self.__on_update)
        self.battery.add_listener(self.__on_update)


    @property
    def power_core_consumption_5s(self) -> int:
        downstream = self.provider.provider_power_downstream_5s + self.pv.power_downstream_5s + self.battery.power_downstream_5s
        upstream = self.provider.provider_power_upstream_5s + self.battery.power_upstream_5s + self.heater.power
        return downstream - upstream

    @property
    def power_consumption(self) -> int:
        return self.provider.provider_power + self.battery.power_downstream + self.pv.power_downstream

    @property
    def power_consumption_5s(self) -> int:
        return self.provider.provider_power_5s + self.battery.power_downstream_5s + self.pv.power_downstream_5s

    @property
    def power_consumption_15s(self) -> int:
        return self.provider.provider_power_15s + self.battery.power_downstream_15s + self.pv.power_downstream_15s

    @property
    def power_consumption_1m(self) -> int:
        return self.provider.provider_power_1m + self.battery.power_downstream_1m + self.pv.power_downstream_1m

    @property
    def power_consumption_5m(self) -> int:
        return self.provider.provider_power_5m + self.battery.power_downstream_5m + self.pv.power_downstream_5m

    @property
    def power_green_1m(self) -> int:
        return self.pv.power_downstream_1m + self.battery.power_downstream_1m

    @property
    def power_surplus(self) -> int:
        return self.provider.provider_power_upstream + self.battery.power_upstream

    @property
    def power_surplus_5s(self) -> int:
        return self.provider.provider_power_upstream_5s + self.battery.power_upstream_5s

    @property
    def power_surplus_15s(self) -> int:
        return self.provider.provider_power_upstream_15s + self.battery.power_upstream_15s

    @property
    def power_surplus_1m(self) -> int:
        return self.provider.provider_power_upstream_1m + self.battery.power_upstream_1m

    @property
    def power_surplus_5m(self) -> int:
        return self.provider.provider_power_upstream_5m + self.battery.power_upstream_5m

    @property
    def power_surplus_60m(self) -> int:
        return self.provider.provider_power_upstream_60m + self.battery.power_upstream_60m

    def __on_update(self):
        [listener() for listener in self.__listeners]

    def add_listener(self, listener):
        self.__listeners.add(listener)

    def start(self):
        pass

    def stop(self):
        self.__is_running = False


