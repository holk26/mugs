#!/bin/bash
set -e

# If a custom command is passed (e.g. celery worker), run it directly so the
# same image can be reused for the Django web service and Celery workers.
if [ $# -gt 0 ]; then
    exec "$@"
fi

if [ -z "$AWS_S3_ENDPOINT_URL" ]; then
    mkdir -p "${MEDIA_ROOT:-/app/media}"
fi

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py ensure_admin

exec gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 4
