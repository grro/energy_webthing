from battery import Battery
from time import sleep


b = Battery('http://10.1.33.100', r"C:\temp",  '192.168.1.99')
b.add_listener(lambda: print("akku level " + str(b.state_of_charge) + " %"))
b.start()
sleep(199999)
