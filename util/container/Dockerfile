FROM ubuntu:22.04

# Install verilator dependencies and python for cocotb and pytest
RUN apt-get update && \
    apt-get -y install \
    git \
    autoconf \
    help2man \
    perl \
    python3 \
    python3-pip \
    make \
    flex \
    bison \
    g++ \
    libfl2 \
    libfl-dev \
    curl \
    openjdk-11-jre-headless openjdk-11-jdk-headless \
    wget \
    tar \
    gnupg2 \
    software-properties-common \
    lsb-release \
    git \
    tar \
    unzip \
    python3-pip

# Verible
ENV VLT_ROOT /usr/local/share/verilator
ENV VERIBLE_VERSION 0.0-3644-g6882622d

# Install Verilator
RUN git clone https://github.com/verilator/verilator && \
  cd verilator && \
  git checkout stable && \
  unset VERILATOR_ROOT && \
  autoconf && \
  ./configure && \
  make -j$(nproc) && \
  make install && \
  cd .. && \
  rm -rf verilator && \
  rm -rf /root/.cache

# Get bender binary
# Bender
RUN cd /usr/bin && curl --proto '=https' --tlsv1.2 https://pulp-platform.github.io/bender/init -sSf | sh -s 0.28.1 && cd /

RUN wget https://github.com/chipsalliance/verible/releases/download/v${VERIBLE_VERSION}/verible-v${VERIBLE_VERSION}-linux-static-x86_64.tar.gz && \
    mkdir tempdir && \
    tar -x -f verible-v${VERIBLE_VERSION}-linux-static-x86_64.tar.gz --strip-components=1 -C tempdir && \
    cp -rn tempdir/bin/* ./bin/ && \
    rm -rf verible-v${VERIBLE_VERSION}-linux-static-x86_64.tar.gz tempdir

# Install python dependencies
WORKDIR /repo
COPY requirements.txt .
RUN pip install -r requirements.txt
