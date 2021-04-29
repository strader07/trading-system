#!/bin/bash

for arg; do
    kubectl apply -f $arg
done
