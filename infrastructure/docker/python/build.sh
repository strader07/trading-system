#! /bin/sh

# exit if a command fails
set -xe

LC_ALL=en_US.UTF-8
LANG=en_US.UTF-8
LANGUAGE=en_US.UTF-8

apk add --no-cache \
    ca-certificates\
    tzdata \
    alpine-sdk \
    bash \
    jq \
    openssl-dev \
    libffi \
    libffi-dev \
    py3-setuptools

pip install --upgrade pip

# Install yq
wget -O /tmp/yq "https://github.com/mikefarah/yq/releases/download/2.2.1/yq_linux_amd64" && install -m 755 /tmp/yq /usr/local/bin/yq

# Clean-up packages
rm -rf /tmp/*
