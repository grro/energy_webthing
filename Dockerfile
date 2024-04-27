FROM python:3-slim-bookworm

ENV meter_addr_pv http://192.168.1.11:8873
ENV meter_addr_provider  http://192.168.1.11:8875

RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN ls
RUN pip install -r requirements.txt

CMD python /etc/app/energy_webthing.py 8800  $meter_addr_pv $meter_addr_provider



