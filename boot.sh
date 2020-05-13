#!/bin/sh
. .venv/bin/activate
sleep 8
python app.py
exec gunicorn -b :8050 --access-logfile - --error-logfile -  --timeout 240 app:server
