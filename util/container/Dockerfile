FROM ubuntu:22.04 AS base

# Install verilator dependencies and python for cocotb and pytest
RUN apt-get update && apt-get install -y lsb-release wget software-properties-common gnupg curl && \
  wget https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && ./llvm.sh 17 && rm llvm.sh && \
  apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y \
  build-essential \
  device-tree-compiler \
  git \
  gnupg2 \
  lsb-release \
  software-properties-common \
  tar \
  unzip \
  wget \
  zlib1g-dev \
  zsh \
  vim \
  nano \
  openjdk-11-jre-headless openjdk-11-jdk-headless \
  mlir-17-tools clang-format-17 python3 \
  help2man perl make autoconf g++ flex bison ccache \
  libgoogle-perftools-dev numactl perl-doc \
  libfl2 libfl-dev zlib1g zlib1g-dev \
  sbt \
  python3-pip && \
  # create symbolic links for all *-17 binaries
  for f in /usr/bin/*-17; do ln -s $f ${f%-17}; done && \
  # Update pip for git installs
  pip3 install --upgrade pip

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

ENV VLT_ROOT /usr/local/share/verilator
ENV VERIBLE_VERSION 0.0-3644-g6882622d

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
