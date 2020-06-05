# Index of Multiple Deprivation and GP surgery mapping tool

## About the application

> This is a small [Dash](https://dash.plotly.com/) application written in Python for visualising GP surgeries and their Primary Care Networks (PCNs) across the UK alongside the [Index of Multiple Deprivation](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019).
> The intention of this tool is to help identify and differentiate between GP surgeries in deprived areas and those in non-deprived areas to help tackle the inverse care law.
> The application is under an MIT license.

## Heroku deployment

> A version of the app has been deployed to a Heroku server [here](https://iomd-gp-map.herokuapp.com/).

## Project structure

> The main Dash app is situated in [app.py](/app.py).
> The mapping functions are situated in [mapping.py](/mapping.py)
> The data is situated in [/data](/data/)

# Running it locally

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

## Heroku

Set up a virtual environment

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the app

```bash
heroku local
```

Note: Make sure you have a .env file or environment variable with you mapbox token as MAPBOX_ACCESS_TOKEN

### TO DO

- Dockerise
- Setup PostGIS backend rather than reading data in from .pkl
- Some frontend CRUD functionality with backend
- API for backend data

## Contributing

See [here](/CONTRIBUTING.MD) on how to contribute.