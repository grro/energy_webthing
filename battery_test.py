from battery import Battery
from time import sleep


b = Battery("http://10.1.33.100", "C:\\temp")
b.start()
sleep(2)

while True:
   # print("akku level " + str(b.charge_level))
   # print("akku today " + str(b.energy_down_today))
   # print("akku year " + str(b.energy_down_estimated_year))
   # print("status " + b.status)
    sleep(1)
    print(b.status)
