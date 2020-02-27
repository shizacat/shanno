#!/bin/bash

set -o errexit

# Run
python3 ./manage.py migrate

# Create super admin
if [[ -n "${SH_ADMIN_USERNAME}" ]] && \
   [[ -n "${SH_ADMIN_PASSWORD}" ]] && \
   [[ -n "${SH_ADMIN_EMAIL}" ]]; \
then
	python3 manage.py ensure_adminuser \
		--username ${SH_ADMIN_USERNAME} \
		--password ${SH_ADMIN_PASSWORD} \
		--email ${SH_ADMIN_EMAIL}
fi

gunicorn \
	--bind="0.0.0.0:${SH_PORT:-8000}" \
	--workers="${SH_WORKERS:-1}" \
	--pythonpath=server server.wsgi \
	--timeout 300
