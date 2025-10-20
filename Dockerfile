FROM python:3-alpine

ENV port 8343
ENV provider  http://example.org
ENV pv_module1 http://example.org
ENV pv_module2 http://example.org
ENV pv_module3 http://example.org
ENV pv_module4 http://example.org


RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN pip install -r requirements.txt

CMD python /etc/app/energy_webthing.py $port $provider $pv_module1 $pv_module2 $pv_module3 $pv_module4



