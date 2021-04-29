#!/bin/bash

set -e

SECRETNAME=dockerhub
USERNAME=
PW=

kubectl create secret docker-registry $SECRETNAME \
  --docker-username=$USERNAME \
  --docker-password=$PW
