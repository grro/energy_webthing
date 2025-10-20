import sys
import logging
from webthing import (MultipleThings,  WebThingServer)
from provider import Provider, ProviderThing
from pv import Pv, PvThing
from battery import Battery, BatteryThing
from energy import Energy, EnergyThing



def run_server(port: int,
               meter_addr_provider: str,
               pv_module1: str,
               pv_module2: str,
               pv_module3: str,
               pv_module4: str):

    provider = Provider(meter_addr_provider)
    pv = Pv(pv_module1, pv_module2, pv_module3, pv_module4)
    battery = Battery()
    energy = Energy(provider, pv, battery)
    server = WebThingServer(MultipleThings([ProviderThing(provider), PvThing(pv), BatteryThing(battery), EnergyThing(energy)], "energy"), port=port, disable_host_validation=True)
    try:
        logging.info('starting the server http://localhost:' + str(port) + " (provider meter=" + meter_addr_provider + ")")
        provider.start()
        pv.start()
        battery.start()
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping the server')
        provider.stop()
        pv.stop()
        server.stop()
        battery.stop()
        logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(name)-20s: %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger('tornado.access').setLevel(logging.ERROR)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    run_server(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
