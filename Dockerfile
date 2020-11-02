# Use the official image as a parent image.
FROM rust:latest

# Set the working directory.
WORKDIR /home/futil

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . .

# Run the command inside your image filesystem.
RUN cargo install runt vcdump
RUN cargo build

RUN apt update -y
RUN apt install -y python3-pip verilator jq
RUN pip3 install flit numpy
WORKDIR /home/futil/fud
RUN pwd
RUN ls
RUN FLIT_ROOT_INSTALL=1 flit install --symlink

# reset workdir
WORKDIR /home/futil
