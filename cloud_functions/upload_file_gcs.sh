#!/bin/bash

FILENAME=om.csv

gsutil -m cp $FILENAME gs://om_analytics/$FILENAME
