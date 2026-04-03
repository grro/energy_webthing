import sys
import logging
from time import sleep

from webthing import (MultipleThings,  WebThingServer)
from provider import Provider, ProviderThing
from pv import Pv, PvThing
from battery import Battery, BatteryThing
from energy import Energy, EnergyThing
from energy_mcp import EnergyMCPServer


def run_server(port: int,
               meter_addr_provider: str,
               pv_all: str,
               pv_module1: str,
               pv_module2: str,
               pv_module3: str,
               battery: str,
               directory: str,
               mqtt_addr: str):

    provider = Provider(meter_addr_provider)
    pv = Pv(pv_all, pv_module1, pv_module2, pv_module3, directory)
    battery = Battery(battery, directory, mqtt_addr)
    energy = Energy(provider, pv, battery)

    mcp_server = EnergyMCPServer(port+1, energy, pv)
    server = WebThingServer(MultipleThings([ProviderThing(provider), PvThing(pv), BatteryThing(battery), EnergyThing(energy)], "energy"), port=port, disable_host_validation=True)

    try:
        provider.start()
        pv.start()
        battery.start()
        energy.start()
        mcp_server.start()
        logging.info('Webthing Server running on http://localhost:' + str(port))
        server.start()
        sleep(5555)
    except KeyboardInterrupt:
        logging.info('stopping the server')
        provider.stop()
        pv.stop()
        battery.stop()
        energy.stop()
        mcp_server.stop()
        server.stop()
        logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(name)-20s: %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger('tornado.access').setLevel(logging.ERROR)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    run_server(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9])
