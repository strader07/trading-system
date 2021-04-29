#!/bin/bash
set -e

for i in `kubectl get pods | ag error | cut -d '-' -f1,2,3,4 | uniq`; do
    lmarket=`echo $i | cut -d '-' -f1`
    market=`echo ${lmarket^^}`
    file=`echo $i | cut -d '-' -f2,3,4`.yaml

    rerun=reruns/$market
    mkdir -p $rerun

    kubectl delete -f raw_jobs/$market/$file
    mv raw_jobs/$market/$file $rerun/
done
