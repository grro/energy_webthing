# energy_webthing



## example

sudo docker run --name energy --network host  --mount type=bind,source="/etc/energy",target=/app/energy -e port=8877 -e meter_addr_pv='http://10.1.11.91' -e meter_addr_provider='http://10.1.11.92' -e directory='/app/energy ' grro/energy_webthing:0.0.18