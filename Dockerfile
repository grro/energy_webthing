FROM python:3-alpine

ENV port 8343
ENV pv http://example.org
ENV pv_ch1 http://example.org
ENV pv_ch2 http://example.org
ENV pv_ch3 http://example.org
ENV provider  http://example.org
ENV directory /etc/energy
ENV min_pv_power 400

RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN pip install -r requirements.txt

CMD python /etc/app/energy_webthing.py $port $provider $pv $pv_ch1 $pv_ch2 $pv_ch3 $directory $min_pv_power



