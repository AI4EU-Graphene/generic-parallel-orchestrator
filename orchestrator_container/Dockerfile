FROM debian:buster-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=linux
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

COPY orchestrator_container/Pipfile .
COPY orchestrator_container/Pipfile.lock .
COPY orchestrator_container/src ./src
COPY orchestrator_container/orchestrator.proto .

RUN set -ex \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev build-essential protobuf-compiler \
    && python3 -m pip install pip --upgrade \
    && python3 -m pip install pipenv setuptools grpcio grpcio-tools --upgrade \
    && pipenv install \
    && apt-get remove -y build-essential python3-dev \
    && apt-get autoremove -y \
    && apt-get clean -y

RUN echo "=== FINAL APP STRUCTURE ===" && find /app

RUN pipenv run python -m grpc_tools.protoc --python_out=/app/ --proto_path=/app/ --grpc_python_out=/app/ /app/orchestrator.proto

CMD ["pipenv", "run", "python3", "-m", "ai4eu.orchestratorservice"]
