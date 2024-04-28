# energy_webthing



## example

sudo docker run --name energy --network host -e port=8877 -e meter_addr_pv='http://10.1.11.91' -e meter_addr_provider='http://10.1.11.92'  grro/energy_webthing:0.0.11