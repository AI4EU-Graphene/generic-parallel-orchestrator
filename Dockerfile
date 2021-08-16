# Dockerfile for building generic-serial-orchestrator image from Ubuntu 18.04 image
FROM debian:buster-slim

ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app/

WORKDIR /app

COPY Pipfile ./
COPY Pipfile.lock ./

# do this all in one to keep the image small
RUN set -ex \
    && apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev build-essential protobuf-compiler \
    && python3 -m pip install pip --upgrade \
    && python3 -m pip install pipenv setuptools --upgrade \
    && pipenv install \
    && apt-get remove -y build-essential python3-dev \
    && apt-get autoremove -y \
    && apt-get clean -y

COPY orchestrator_container/src /app
COPY orchestrator_container/orchestrator.proto /app

RUN find /app

CMD ["pipenv", "run", "python3", "-m", "ai4eu.orchestratorservice"]

