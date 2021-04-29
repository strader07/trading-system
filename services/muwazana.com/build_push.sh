#!/bin/bash
VERSION="${1:-latest}"
docker build -t eu.gcr.io/strange-metrics-258802/muwazana:$VERSION .
docker push eu.gcr.io/strange-metrics-258802/muwazana:$VERSION
