#!/bin/bash
SOURCE_IMAGE_ID=$1
VERSION=$2
docker tag $SOURCE_IMAGE_ID eu.gcr.io/strange-metrics-258802/lab:$VERSION
docker push eu.gcr.io/strange-metrics-258802/lab:$VERSION
