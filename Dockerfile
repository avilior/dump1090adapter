FROM python:3.6-slim

LABEL maintainer="avi@lior.org"

ARG BIND_HOST=0.0.0.0
ARG LISTEN_PORT=80

ENV PYTHONBUFFERED=1
ENV HOST=$BIND_HOST
ENV PORT=$LISTEN_PORT

ENV DB_URL=sqlite://localhost/../database/dump1090db.sqlite
ENV PUBLIC_PATH=../public
ENV DUMPHOST=0.0.0.0
ENV DUMPPORT=30003


EXPOSE $LISTEN_PORT/tcp

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


COPY ./dump1090adapter .

ENTRYPOINT ["python","-m", "app"]