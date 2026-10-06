# One consolidated container with EMANE built from source.
# Built from source because the official EMANE packages are x86 only and
# this machine is ARM (Apple Silicon). The same file works on x86 Linux.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates build-essential autoconf automake libtool pkg-config \
      libxml2-dev libprotobuf-dev protobuf-compiler libpcap-dev libpcre3-dev \
      uuid-dev python3 python3-dev python3-pip python3-setuptools \
      python3-protobuf python3-lxml iproute2 iputils-ping tcpdump \
      net-tools procps \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/adjacentlink/emane.git /opt/emane-src \
    && cd /opt/emane-src && ./autogen.sh \
    && ./configure --prefix=/usr \
    && make -j"$(nproc)" && make install \
    && cd src/python && make && python3 setup.py install \
    && ldconfig

RUN pip3 install --no-cache-dir "networkx>=3.0"

WORKDIR /work
CMD ["bash"]
