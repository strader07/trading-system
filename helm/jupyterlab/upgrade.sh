#!/bin/bash
RELEASE=jhub
NAMESPACE=research

helm2 upgrade --install $RELEASE jupyterhub/jupyterhub \
  --namespace $NAMESPACE \
  --version=0.8.2 \
  --values config.yaml \
  --timeout 600
