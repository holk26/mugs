#!/bin/sh
envsubst '$VITE_API_URL' < /etc/nginx/conf.d/default.conf > /tmp/nginx.conf
mv /tmp/nginx.conf /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'
