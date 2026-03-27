# Free Demo Deployment Guide

This guide is for a lightweight public demo where users can try the UI for free.

## 1) Local demo mode (no processed data required)

```bash
pip install -r requirements-demo.txt
```

PowerShell:

```powershell
$env:DEMO_MODE="1"
streamlit run platform/patient_app.py
```

Clinician view:

```powershell
$env:DEMO_MODE="1"
streamlit run platform/clinician_dashboard.py
```

## 2) Hugging Face Spaces (free tier)

Use a **Streamlit Space** and connect this GitHub repository.

Recommended Space setup:

- SDK: `streamlit`
- Python: `3.10`
- App file: `platform/patient_app.py`
- Requirements file: `requirements-demo.txt`

In Space Variables / Secrets, add:

- `DEMO_MODE=1`

Notes:

- Demo mode serves synthetic data only.
- Heavy training pipeline and full model artifacts should remain local or on dedicated infra.

## 3) Full local usage for advanced users

For full pipeline (feature extraction, training, causal analysis):

```bash
pip install -r requirements.txt
python -m src.data.make_dataset
python -m src.features.sleep_features
python -m src.models.brain_age_model
python -m src.models.causal_inference
```
