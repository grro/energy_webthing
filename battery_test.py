import logging
from battery import Battery
from time import sleep


logging.basicConfig(format='%(asctime)s %(name)-20s: %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('tornado.access').setLevel(logging.ERROR)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)


b = Battery('http://10.1.33.100', r"C:\temp",  '192.168.1.99')
b.add_listener(lambda: print(str(b.status)))
b.start()
sleep(199999)
