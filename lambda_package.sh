#!/bin/bash
#create delplyment package:
#this should be ran on arm64 mac

PYTHON_VERSION=python3.12
VENV=purerackdiagram_env_lambda
VENV_LOCAL=purerackdiagram_env_local
rm lambda.zip
rm -rf $VENV
rm -rf $VENV_LOCAL


$PYTHON_VERSION -m venv $VENV_LOCAL
source ./$VENV_LOCAL/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
#Include extra packages already found in the amazon environment so we can run locally
pip install -r requirements_venv_local.txt --upgrade
$PYTHON_VERSION update_config.py
deactivate

# Now for the one that will send to amazon
$PYTHON_VERSION -m venv $VENV
source ./$VENV/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
deactivate
cd $VENV/lib/$PYTHON_VERSION/site-packages
zip -r ../../../../lambda.zip yaml --exclude '*.pyc' --exclude '*__pycache__*'
cd ../../../../
zip -r lambda.zip lambdaentry.py purerackdiagram vssx -i '*.png' '*.py' '*.ttf' '*.yaml' '*.xml' '*.zip'


