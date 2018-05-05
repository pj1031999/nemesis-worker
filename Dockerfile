FROM debian:stretch-slim
LABEL maintainer "Paweł Jasiak contact@jasiak.xyz"

RUN apt-get update && apt-get install -y    \
        build-essential \
        gcc \
        g++ \
        libc6-dev   \
        libseccomp-dev  \
        seccomp \
        protobuf-compiler   \
        libprotobuf-dev     \
        python3-protobuf    \
        libzmq5     \
        python3-zmq \
        git \
        --no-install-recommends \
        && rm -rf /var/lib/apt/lists/* 

WORKDIR /root
COPY . /root
RUN make install

ENV PATH=/usr/local/bin:/usr/local/sbin:$PATH
ENV PYTHONPATH=/usr/local/lib/nemesis/python:$PYTHONPATH

ENTRYPOINT ["worker"]
