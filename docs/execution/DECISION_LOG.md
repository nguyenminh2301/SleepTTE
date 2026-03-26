# SleepTTE Decision Log

## D-2026-03-27-01
- Decision: Use incremental delivery (Round 4.x) instead of broad unbounded refactor.
- Reason: Reduce risk, keep measurable progress, avoid losing functional stability.
- Impact: Each round must include code + tests + docs + progress update.

## D-2026-03-27-02
- Decision: Start Round 4 with configuration backbone first.
- Reason: All modules depend on config, and future API/UI features require stable configuration contracts.
- Impact: `load_config` becomes layered and validated before adding larger features.

## D-2026-03-27-03
- Decision: Keep backward-compatible default path `config/config.yaml` and add optional `SLEEPTTE_ENV` overlays.
- Reason: Avoid breaking all current entrypoints while enabling dev/prod split immediately.
- Impact: No command change required for existing workflows; environment-specific behavior can be enabled progressively.

## D-2026-03-27-04
- Decision: Introduce API prediction endpoint with a proxy predictor first.
- Reason: Establish stable request/response contract early, then swap inference backend without breaking clients.
- Impact: API consumers can integrate now; model-serving upgrade is planned as M4.2-03.

## D-2026-03-27-05
- Decision: Move API prediction to artifact-based inference with configurable fallback policy.
- Reason: Production requires real model inference; development still needs resilient behavior when artifacts are absent.
- Impact:
  - `api.brain_age_delta_artifact` defines serving artifact path.
  - `api.allow_proxy_fallback` controls strictness (`503` vs proxy fallback).

## D-2026-03-27-06
- Decision: Apply API-key guard to `/config` and `/predict/brain-age` only.
- Reason: Keep `/health` open for orchestration probes while protecting sensitive operational/model endpoints.
- Impact: Supports secure rollout now without blocking infrastructure health checks.

## D-2026-03-27-07
- Decision: Use JSONL append-only event logging for initial interaction tracking.
- Reason: Minimal dependency, robust write pattern, easy downstream ingestion/aggregation.
- Impact: Quick visibility into platform usage while keeping future migration path to centralized logging open.

## D-2026-03-27-08
- Decision: Add dedicated model metadata endpoint instead of embedding all details in `/config`.
- Reason: Separate operational configuration from runtime model state and artifact details.
- Impact: UI/clients can fetch model serving metadata directly with a stable contract.
