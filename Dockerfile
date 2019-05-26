FROM python:3.6-slim

ENV PYTHONBUFFERED=1

EXPOSE 4000/tcp

RUN mkdir -p /public \
    && mkdir -p /app

WORKDIR /app

COPY requirements.txt ./

RUN set -eux \
    && apt-get update \
    && apt-get install --yes --only-upgrade openssl ca-certificates \
    && apt-get install --yes --no-install-recommends \
        build-essential \
    && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip \
    && apt-get purge --yes build-essential \
    && apt-get autoremove --yes \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


COPY ./dump1090adapter /app/
