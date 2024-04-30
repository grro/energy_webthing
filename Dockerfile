FROM python:3.10-alpine

ENV port 8343
ENV pv http://example.org
ENV provider  http://example.org
ENV directory /etc/energy

RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN pip install -r requirements.txt

CMD python /etc/app/energy_webthing.py $port $provider $pv $directory



