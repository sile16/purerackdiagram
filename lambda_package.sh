#!/bin/bash
#create delplyment package:
#this should be ran on arm64 mac

PYTHON_VERSION=python3.12
VENV=purerackdiagram_env
rm lambda.zip

$PYTHON_VERSION -m venv $VENV
python3 update_config.py
source ./purerackdiagram_env/bin/activate
pip install -r requirements.txt
deactivate
cd $VENV/lib/PYTHON_VERSION/site-packages
zip -r ../../../../lambda.zip .
cd ../../../../
zip lambda.zip lambdaentry.py lambda/


