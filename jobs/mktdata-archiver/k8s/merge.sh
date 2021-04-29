#!/bin/bash

DIR=$1

for i in `/bin/ls $DIR`; do
    mv $DIR/$i/* $DIR/
    rmdir $DIR/$i
done
