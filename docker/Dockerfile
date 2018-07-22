FROM python:2.7.15-alpine3.7

RUN apk add git gcc build-base linux-headers libffi libffi-dev openssl openssl-dev tini
RUN mkdir /ultros

COPY . /ultros
WORKDIR /ultros

RUN pip install -r requirements.txt
RUN pip install -r requirements-contrib.txt

VOLUME ["/ultros/config", "/ultros/plugins"]

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "run.py"]