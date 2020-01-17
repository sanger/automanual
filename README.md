# AutoManual

This script will automatically perform a manual QC on the required runs.

## Requirements

* python 3.8
* pipenv

## Running

The following config is required for this script, place these in a `.env` file before continuing:

```shell
MLWH_DB_USER=
MLWH_DB_PASSWORD=
MLWH_DB_HOST=
MLWH_DB_PORT=
MLWH_DB_DBNAME=
SS_DB_USER=
SS_DB_PASSWORD=
SS_DB_HOST=
SS_DB_PORT=
SS_DB_DBNAME=
SS_URL_HOST=
```

### Using `pipenv`

This project uses pipenv to manage the evironment and python packages:

1. To craete the virtual environment run `pipenv shell`
1. Once in the virtual environment, run `pipenv install`
1. To run the script, `python main.py`
