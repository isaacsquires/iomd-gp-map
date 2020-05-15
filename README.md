# PCN-mapping-tool

## Python

Set up a virtual environment

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the app

```bash
python app.py
```

Note: Make sure you have a .env file or environment variable with you mapbox token as MAPBOX_ACCESS_TOKEN

## Docker

To build Docker container

```bash
docker build .
```

To run

```bash
docker run .
```