#!/bin/sh
set -e
envsubst '$VITE_API_URL' < /etc/nginx/conf.d/default.conf > /tmp/nginx.conf
mv /tmp/nginx.conf /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
