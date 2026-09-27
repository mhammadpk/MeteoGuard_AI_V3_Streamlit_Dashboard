# MeteoGuard AI V3.1 Dashboard

An explainable meteorological observation-quality monitoring and alert-triage prototype prepared for hackathon demonstration.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Included files

- `app.py` — Streamlit dashboard
- `alerts.csv` — prepared alert-review records
- `metrics.csv` — detection evaluation results
- `extremes.csv` — legitimate-extreme preservation results
- `requirements.txt` — Python dependencies

## Scope

The prototype uses public NOAA observations and controlled sensor-fault scenarios. Proposed values are decision-support recommendations that require human review. This is not an operational NCM system.
