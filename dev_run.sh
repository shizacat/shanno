#!/bin/bash

# Run development environment

VBASE=venv
APPBASE=source/server

export SH_DEBUG=True

. ${VBASE}/bin/activate

python3 ${APPBASE}/manage.py migrate
python3 ${APPBASE}/manage.py runserver 0:8000
