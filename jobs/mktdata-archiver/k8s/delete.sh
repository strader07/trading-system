#!/bin/bash

for arg; do
    kubectl delete -f $arg
done
