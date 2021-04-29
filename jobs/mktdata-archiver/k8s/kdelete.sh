#!/bin/bash

MARKET=$1

function delete() {
    MARKET=$1
    for i in `kubectl get job | ag $MARKET | cut -d ' ' -f1`; do 
        kubectl delete job $i
    done
}

while true; do
    read -p "Delete $MARKET? " yn
    case $yn in
        [Yy]* ) delete $MARKET; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
