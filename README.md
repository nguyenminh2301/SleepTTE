# SleepTTE

Precision sleep analytics for brain aging research, with feature extraction, predictive modeling, and target trial emulation.

## What this repository currently includes

- Data pipeline to generate/load raw data and produce processed tables.
- Actigraphy-based sleep feature extraction.
- Brain-aging model pipeline with automatic model selection (round 4):
  - Baseline: `DummyRegressor`
  - Candidates: `Ridge`, `ElasticNet`, `RandomForestRegressor`, `GradientBoostingRegressor`
  - Selection criterion: lowest out-of-fold (OOF) MAE.
  - Candidate list / CV settings are configurable in `config/config.yaml` (`brain_modeling`).
- Causal inference utilities (propensity score, IPTW, covariate balance, bootstrap CI).
- Streamlit apps for patient and clinician views.

## Project structure

```text
SleepTTE/
  config/
    config.yaml
  docs/
  outputs/
    figures/
    reports/
    tables/              # generated during modeling runs
  platform/
    patient_app.py
    clinician_dashboard.py
  scripts/
  src/
    data/
      make_dataset.py
      utils.py
    features/
      sleep_features.py
    models/
      brain_age_model.py
      causal_inference.py
    utils/
      stats.py
    visualization/
      plots.py
  tests/
```

## Requirements

- Python 3.9+
- Recommended: virtual environment

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional (for static Plotly image export):

```bash
pip install kaleido
```

If `kaleido` is not installed, Plotly figures are saved as `.html` fallback files.

## Quick start

### 1) Generate/load processed data

```bash
python -m src.data.make_dataset
```

### 2) Extract sleep features

```bash
python -m src.features.sleep_features
```

### 3) Train/evaluate brain-aging models (auto model selection)

```bash
python -m src.models.brain_age_model
```

Main outputs:

- `outputs/tables/model_performance.csv`
- `outputs/tables/model_selection_leaderboard.csv`
- `outputs/tables/brain_aging_predictions.csv`
- `outputs/models/brain_age_delta_model.joblib` (and other biomarker artifacts)

Configuration (round 4):

- `brain_modeling.candidate_models`: limit which models are evaluated in auto mode.
- `brain_modeling.cv_folds`: OOF fold count (auto-capped by sample size).
- `brain_modeling.random_seed`, `brain_modeling.n_jobs`.
- Multi-environment config overlay:
  - Base: `config/config.yaml`
  - Overlays: `config/dev.yaml`, `config/prod.yaml`
  - Activate with env var: `SLEEPTTE_ENV=dev` (or `prod`)

### 4) Run target trial emulation

```bash
python -m src.models.causal_inference
```

Main outputs:

- `outputs/tables/comparative_effectiveness.csv`
- `outputs/figures/love_plot_*.(png/html)`
- `outputs/figures/comparative_effectiveness_forest.(png/html)`

## Run Streamlit apps

```bash
streamlit run platform/patient_app.py
streamlit run platform/clinician_dashboard.py
```

## Run API Skeleton (Round 4.2)

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Initial endpoints:

- `GET /health`
- `GET /config`
- `POST /predict/brain-age`
- `GET /model/brain-age/metadata`

Notes:

- `POST /predict/brain-age` uses the trained artifact at `api.brain_age_delta_artifact`.
- If artifact is missing, behavior depends on config:
  - `api.allow_proxy_fallback=true`: fallback proxy predictor.
  - `api.allow_proxy_fallback=false`: return `503`.
- API auth guard:
  - `api.require_api_key=true` enables header check on `/config` and `/predict/brain-age`.
  - Send header `X-API-Key: <key>`.
  - You can override configured key with env var `SLEEPTTE_API_KEY`.

## Testing

```bash
pytest -q
```

## Progress Tracking

- Task board: `docs/execution/TASK_BOARD.md`
- Progress log: `docs/execution/PROGRESS_LOG.md`
- Decision log: `docs/execution/DECISION_LOG.md`

## Interaction Event Logs

- Platform events are appended to `logs/events.log` in JSONL format.
- Current tracked events include page views and key data-load actions in patient/clinician apps.

## Notes on current behavior

- Model metrics now report both train and OOF performance to reduce optimistic bias.
- `brain_age_model.py` uses OOF MAE for model selection per biomarker.
- For small synthetic datasets, low/negative OOF R2 can still occur and does not necessarily indicate a pipeline bug.

## License

MIT (see `LICENSE`).
