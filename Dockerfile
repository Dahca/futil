# Use the official image as a parent image.
FROM rust:latest

# Install dependencies
RUN cargo install runt vcdump
RUN apt update -y
RUN apt install -y python3-pip verilator jq
RUN pip3 install flit numpy

# Set the working directory.
WORKDIR /home/futil

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . .

RUN cargo build

WORKDIR /home/futil/fud
RUN FLIT_ROOT_INSTALL=1 flit install --symlink
RUN mkdir -p /root/.config
ENV PATH=$PATH:/root/.local/bin
RUN fud config global.futil_directory /home/futil

# reset workdir
WORKDIR /home/futil
