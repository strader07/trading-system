#! /bin/sh

# exit if a command fails
set -xe

LC_ALL=en_US.UTF-8
LANG=en_US.UTF-8
LANGUAGE=en_US.UTF-8
PROTOBUF_REVISION=3.6.0
ALPINE_GLIBC_BASE_URL=https://github.com/andyshinn/alpine-pkg-glibc/releases/download
ALPINE_GLIBC_PACKAGE_VERSION=2.27-r0
ALPINE_GLIBC_BASE_PACKAGE_FILENAME=glibc-$ALPINE_GLIBC_PACKAGE_VERSION.apk
ALPINE_GLIBC_BIN_PACKAGE_FILENAME=glibc-bin-$ALPINE_GLIBC_PACKAGE_VERSION.apk
ALPINE_GLIBC_I18N_PACKAGE_FILENAME=glibc-i18n-$ALPINE_GLIBC_PACKAGE_VERSION.apk

apk add --no-cache \
    alpine-sdk \
    ca-certificates \
    tzdata \
    autoconf \
    automake \
    libstdc++ \
    libtool \
    unzip \
    wget

curl -sLO https://github.com/google/protobuf/releases/download/v${PROTOBUF_REVISION}/protoc-${PROTOBUF_REVISION}-linux-x86_64.zip \
    && unzip protoc-${PROTOBUF_REVISION}-linux-x86_64.zip -d /usr/local \
    && chmod +x /usr/local/bin/protoc \
    && chmod -R 755 /usr/local/include/ \
    && rm protoc-${PROTOBUF_REVISION}-linux-x86_64.zip

curl -sL \
        -O "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        -O "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        -O "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_I18N_PACKAGE_FILENAME" \
    && apk add --no-cache --allow-untrusted \
        "$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_I18N_PACKAGE_FILENAME" \
    && /usr/glibc-compat/bin/localedef --force --inputfile POSIX --charmap UTF-8 C.UTF-8 || true \
    && echo "export LANG=C.UTF-8" > /etc/profile.d/locale.sh \
    && rm "$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_I18N_PACKAGE_FILENAME"

# Install grpc protobuf generator
go get -u -v github.com/grpc-ecosystem/grpc-gateway/protoc-gen-grpc-gateway
go get -u -v github.com/golang/protobuf/protoc-gen-go

# Install golangci-lint
go get -u -v github.com/golangci/golangci-lint/cmd/golangci-lint

# Install yq
wget -O /tmp/yq "https://github.com/mikefarah/yq/releases/download/2.2.1/yq_linux_amd64" && install -m 755 /tmp/yq /usr/local/bin/yq

# Clean-up packages
apk del \
    autoconf \
    automake \
    libtool \
    unzip \
    glibc-i18n \
    alpine-sdk \
    ca-certificates \
    tzdata \
    autoconf \
    automake \
    libstdc++ \
    libtool

# Install shared libs
apk add --no-cache \
    git \
    curl \
    bash \
    make
