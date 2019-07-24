#!/bin/bash

# Create development environment

VBASE=venv

python3 -m venv ${VBASE}
. ${VBASE}/bin/activate

pip3 install -r requirements.txt

deactivate
