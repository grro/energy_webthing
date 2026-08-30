FROM python:3-alpine

ENV port 8343
ENV provider  http://noexists.example.org
ENV pv_all http://noexists.example.org
ENV pv_module1 http://noexists.example.org
ENV pv_module2 http://noexists.example.org
ENV pv_module3 http://noexists.example.org
ENV pv_module4 http://noexists.example.org
ENV battery http://noexists.example.org
ENV heater http://noexists.example.org
ENV directory /app/energy
ENV mqtt_addr 192.168.1.99


RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN pip install -r requirements.txt

CMD python /etc/app/run_server.py $port $provider $pv_all $pv_module1 $pv_module2 $pv_module3 $pv_module4 $battery $heater $directory $mqtt_addr



