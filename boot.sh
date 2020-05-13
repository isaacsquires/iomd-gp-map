#!/bin/sh
. .venv/bin/activate
sleep 8
python app.py
exec gunicorn -b :5000 --access-logfile - --error-logfile -  --timeout 240 app:server
