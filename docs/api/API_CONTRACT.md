# SleepTTE API Contract

Last updated: 2026-03-27 (Asia/Saigon)
Base URL (local): `http://localhost:8000`

## Authentication and Identity Headers

- API key header (if enabled): `X-API-Key: <key>`
- Identity headers for role policy (if enabled):
  - `X-User-Id: <user-id>`
  - `X-User-Role: <role>`
- JWT identity mode (optional):
  - `Authorization: Bearer <jwt>`
  - claims configured by:
    - `identity.jwt_user_id_claim`
    - `identity.jwt_role_claim`

## Endpoints

### `GET /health`
- Purpose: liveness + artifact availability.
- Auth: none.
- Response fields:
  - `status`
  - `service`
  - `timestamp_utc`
  - `brain_age_model_artifact_loaded`

### `GET /config`
- Purpose: operational config summary for clients/admin tooling.
- Auth: API key (if configured), role policy key `config` (if enabled).

### `POST /predict/brain-age`
- Purpose: predict brain-age delta.
- Auth: API key (if configured), role policy key `predict_brain_age` (if enabled).
- Request JSON:
```json
{
  "sleep_efficiency": 78.0,
  "sleep_fragmentation_index": 12.0,
  "sleep_regularity_index": 62.0,
  "social_jet_lag": 2.5,
  "age": 68.0
}
```
- Response JSON:
```json
{
  "predicted_brain_age_delta": 1.234,
  "risk_level": "moderate",
  "model_version": "artifact-v1"
}
```

### `GET /model/brain-age/metadata`
- Purpose: artifact/model metadata for UI/debug.
- Auth: API key (if configured), role policy key `model_metadata` (if enabled).

### `GET /events/summary`
- Purpose: aggregate interaction logs.
- Auth: API key (if configured), role policy key `events_summary` (if enabled).
- Query params (optional):
  - `start_time_utc` (ISO-8601)
  - `end_time_utc` (ISO-8601)
  - `event_type`
  - `source`
  - `group_by` (`hourly` or `daily`)
  - `top_n` (limit top categories in `by_event_type` / `by_source`)

## Security Audit Events

- API authorization denials are logged to `api.security_event_log_path`.
- Current event types:
  - `api_auth_failed`
  - `api_role_forbidden`

## Curl Examples

```bash
curl -s http://localhost:8000/health
```

```bash
curl -s -X POST http://localhost:8000/predict/brain-age \
  -H "Content-Type: application/json" \
  -d '{"sleep_efficiency":78,"sleep_fragmentation_index":12,"sleep_regularity_index":62,"social_jet_lag":2.5,"age":68}'
```

```bash
curl -s "http://localhost:8000/events/summary?event_type=patient_page_view&source=patient_app"
```
