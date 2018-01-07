FROM debian:stretch-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       git \
       python-dev \
       python-pip

RUN mkdir /etc/ultros
WORKDIR /etc/ultros

RUN git config --global http.sslVerify false \
    && git clone https://github.com/UltrosBot/Ultros.git .

RUN pip install setuptools \
    && pip install wheel \
    && pip install -r requirements.txt

VOLUME ["/etc/ultros/config", "/etc/ultros/plugins"]

CMD ["python", "run.py"]