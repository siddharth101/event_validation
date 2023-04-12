# Event validation infrastructure

## Websites

[Main event validation website](https://ldas-jobs.ligo.caltech.edu/~dqr/event_validation/)

[Event validation website containing event validation forms](404) (TO BE ADDED)

## Installation

The repo can be installed with pip, i.e. `pip install .`

Alternatively, use conda environment (on CIT) `/home/ronaldas.macas/.conda/envs/eval`

## Usage

To create an event, an example command is given in `event_example.sh` script.

To launch Flask website containing event validation webforms, use gunicorn in /code folder to run `app.py`. Example command:
`gunicorn --reload-extra-file /home/ronaldas.macas/projects/eval/data/events_testing.csv --reload -w 4 -b 127.0.0.1:5000 'app:create_app(url="", wdir="/home/ronaldas.macas/projects/eval", event_list="events_testing.csv", website_md="table_testing.md", notify=0)`

## Contact

Ronaldas Macas (ronaldas.macas@ligo.org) and Sidd Soni (siddharth.soni@ligo.org). 
