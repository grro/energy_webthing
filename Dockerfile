FROM python:3-alpine

ENV port 8343
ENV provider  http://noexists.example.org
ENV pv_all http://noexists.example.org
ENV pv_module1 http://noexists.example.org
ENV pv_module2 http://noexists.example.org
ENV pv_module3 http://noexists.example.org
ENV battery http://noexists.example.org
ENV directory /app/energy


RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN pip install -r requirements.txt

CMD python /etc/app/energy_webthing.py $port $provider $pv_all $pv_module1 $pv_module2 $pv_module3 $battery $directory



