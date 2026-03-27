# SleepTTE Progress Log

## 2026-03-27 06:25 (Asia/Saigon)
- Started Round 4.1 execution.
- Confirmed scope with user: optimize whole system, but execute in controlled milestones to avoid drift.
- Established tracking artifacts under `docs/execution/`.

## 2026-03-27 06:28 (Asia/Saigon)
- Audited current config usage:
  - `load_config()` consumed by `data`, `features`, `brain_age_model`, `causal_inference`.
- Identified gap:
  - single-file config only,
  - no environment overlay,
  - no validation layer,
- no explicit feature flags.

## 2026-03-27 06:35 (Asia/Saigon)
- Implemented layered configuration loading in `src/data/utils.py`:
  - base config + env overlay via `SLEEPTTE_ENV`,
  - deep-merge strategy,
  - fail-fast `validate_config`.
- Added `config/dev.yaml` and `config/prod.yaml` overlays.
- Added `feature_flags` section to `config/config.yaml`.

## 2026-03-27 06:39 (Asia/Saigon)
- Integrated feature flag usage into modeling flow:
  - `enable_model_auto_selection` now controls auto-vs-fixed model mode.
- Added new config loader tests in `tests/test_config_loader.py`.
- Updated README with env overlay usage + progress tracking file locations.

## 2026-03-27 06:44 (Asia/Saigon)
- Verification complete:
  - `pytest -q` => 17/17 tests passed.
  - Runtime overlay check (`env=dev`) confirms overrides:
    - `brain_modeling.cv_folds=3`
    - `causal_inference.bootstrap_iterations=200`
    - `platform.require_authentication=False`
- Round 4.1 marked stable and ready to proceed to Round 4.2.

## 2026-03-27 06:56 (Asia/Saigon)
- Implemented Round 4.2 API skeleton:
  - `src/api/app.py` with endpoints:
    - `GET /health`
    - `GET /config`
    - `POST /predict/brain-age`
  - Request/response schemas added with validation.
  - Added API tests in `tests/test_api_skeleton.py`.
- Updated `requirements.txt` and README with API run command.

## 2026-03-27 07:00 (Asia/Saigon)
- Regression check complete after API addition:
  - `pytest -q` => 20/20 tests passed.
- No breakage detected in existing data/model code paths.

## 2026-03-27 07:12 (Asia/Saigon)
- Implemented persisted model artifacts from training pipeline:
  - `outputs/models/<biomarker>_model.joblib`
  - includes model, scaler, feature names/defaults, metadata.
- API `/predict/brain-age` now uses artifact inference by default.
- Added strict behavior control:
  - `api.allow_proxy_fallback=true` -> fallback proxy when artifact missing
  - `api.allow_proxy_fallback=false` -> return 503
- Added/extended tests:
  - artifact write/read contract
  - API artifact inference
  - API strict missing-artifact behavior.

## 2026-03-27 07:15 (Asia/Saigon)
- Validation complete after M4.2-03:
  - `pytest -q` => 23/23 tests passed.
  - End-to-end training generated real artifacts for 3 biomarkers.

## 2026-03-27 07:24 (Asia/Saigon)
- Implemented M4.2-04 API auth guard:
  - `/config` and `/predict/brain-age` now support API key enforcement.
  - Config keys:
    - `api.require_api_key`
    - `api.api_key` (or env `SLEEPTTE_API_KEY` override)
- Added auth tests:
  - no key => `401`
  - valid key => `200`
- Verification complete:
  - `pytest -q` => 26/26 tests passed.

## 2026-03-27 07:33 (Asia/Saigon)
- Implemented M4.2-05 interaction event tracking:
  - Added shared JSONL logger: `src/utils/event_logger.py`
  - Integrated event hooks:
    - `platform/patient_app.py` (page views, data load status)
    - `platform/clinician_dashboard.py` (page views, roster load status)
  - Added logger unit test: `tests/test_event_logger.py`
- Verification complete:
  - `pytest -q` => 27/27 tests passed.

## 2026-03-27 07:42 (Asia/Saigon)
- Implemented M4.2-06 model metadata endpoint:
  - `GET /model/brain-age/metadata`
  - Returns artifact biomarker, version, trained timestamp, features, selected model, CV metrics.
- Added endpoint tests for:
  - missing artifact (`404`)
  - available artifact metadata (`200`)
- Verification complete:
  - `pytest -q` => 29/29 tests passed.

## 2026-03-27 07:54 (Asia/Saigon)
- Implemented M4.3-01 role policy layer for API:
  - Added optional role enforcement via config (`api.enable_role_policy`).
  - Identity claims headers:
    - `X-User-Id`
    - `X-User-Role`
  - Endpoint-level role requirements driven by `api.role_requirements`.
- Added role-policy tests:
  - missing claims => `401`
  - disallowed role => `403`
  - allowed role => `200`

## 2026-03-27 07:56 (Asia/Saigon)
- Implemented M4.3-02 event aggregation/report utility:
  - Added `src/utils/event_summary.py`
  - Added API endpoint `GET /events/summary`
  - Added tests for summary utility and endpoint behavior.
- Verification complete:
  - `pytest -q` => 35/35 tests passed.

## Next log entry rule
- Every completed coding/testing step must append one timestamped bullet block.
