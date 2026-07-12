#!/bin/bash
set -e

if [ -z "$AWS_S3_ENDPOINT_URL" ]; then
    mkdir -p "${MEDIA_ROOT:-/app/media}"
fi

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 4
