FROM python:3.7.5-buster
LABEL maintainer="IsaacSquires <isaacsquires@me.com"

RUN adduser --disabled-password iomd-gp-map

WORKDIR /home/iomd-gp-map

COPY requirements.txt requirements.txt
RUN python -m venv .venv
RUN .venv/bin/pip install --upgrade pip
RUN .venv/bin/pip install -r requirements.txt

COPY app.py app.py
COPY mapping.py mapping.py
COPY boot.sh boot.sh
COPY data data
RUN chmod +x ./boot.sh

RUN chown -R iomd-gp-map:iomd-gp-map ./
USER iomd-gp-map

EXPOSE 8050
CMD ["./boot.sh"]