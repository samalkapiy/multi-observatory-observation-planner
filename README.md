# Multi-Observatory Astronomical Observation Planner

A Python/FastAPI based project which calcuates the visibility windows and shows visualizations of the target altitudes across multiple ground-based observatory sites. 

## Project structure

```text
multi_mission_observation_planner/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── observatories.py
│   └── planner.py
├── tests/
│   └── test_planner.py
├── requirements.txt
└── README.md
```

## Setup

Python 3.10+ is recommended.

```bash
# Create a Conda environment
conda create -n astro_project python=3.11

# Activate the environment
conda activate astro_project

# Install project dependencies
python -m pip install requirements.txt

```

## Run the API

To run the API, cd to the folder which holds the app scripts, activate the astro_project environment and type:

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

## Example request

Send a POST request to `/plan`:

```json
{
  "event_name": "Example transient",
  "ra_deg": 255.7,
  "dec_deg": 10.2,
  "start_time": "2026-11-05T00:00:00",
  "duration_hours": 12,
  "cadence_minutes": 10,
  "min_altitude_deg": 25,
  "require_astronomical_darkness": true
}
```
## Run the dashboard

To run the dashboard application make sure that you have the API running first. 

Install:
```bash
# create a separate conda environment for the streamlit library
conda create -n steamlit_env python=3.11

#activate the environment
conda activate streamlit_env

#install the necessary libraires to run the dashboard script
python -m pip install streamlit plotly requests pandas

#in a separate terminal cd to where the script are in.activate the streamlit_env envrionment. Make sure FastAPI is already running. Type:
streamlit run dashboard.py
```

This will open a dashboard where the user will be able to enter input parameters to caculate visibility windows for different targets. 

## Run tests

```bash
pytest -q
```
## Citing and Acknowledgement:
Please cite my work when using this code. 

Thank you.