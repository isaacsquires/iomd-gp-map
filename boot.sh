#!/bin/sh
. .venv/bin/activate
sleep 8
exec gunicorn -b :5000 --access-logfile - --error-logfile -  --timeout 480 app:server
