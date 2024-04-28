FROM python:3-alpine

ENV meter_addr_pv http://example.org
ENV meter_addr_provider  http://example.org

RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN pip install -r requirements.txt

CMD python /etc/app/energy_webthing.py 8800 $meter_addr_provider $meter_addr_pv



