# SleepTTE Execution Task Board

Last updated: 2026-03-27 (Asia/Saigon)
Owner: Codex + Minh
Branch: `codex/round3-model-quality-readme`

## Scope Guard
- In scope (current): Round 4.1 foundation (`config`, tracking, validation, feature flags).
- Out of scope (current): Major UI redesign, backend API full implementation, infra deployment.

## Milestones
| ID | Task | Status | Priority | ETA | Notes |
|---|---|---|---|---|---|
| M4.1-01 | Create progress/task logging system in repo | DONE | P0 | 2026-03-27 | `docs/execution/*` created |
| M4.1-02 | Multi-environment config loading (dev/prod overlays) | DONE | P0 | 2026-03-27 | `load_config` supports env overlay |
| M4.1-03 | Config validation for required sections/keys | DONE | P0 | 2026-03-27 | Added `validate_config` fail-fast checks |
| M4.1-04 | Introduce feature flags section in config | DONE | P1 | 2026-03-27 | Added `feature_flags` and first runtime usage |
| M4.1-05 | Automated tests for config loader + validation | DONE | P0 | 2026-03-27 | Added `tests/test_config_loader.py` |
| M4.1-06 | Document config strategy in README | DONE | P1 | 2026-03-27 | README updated |
| M4.1-07 | Verification run (tests + runtime overlay check) | DONE | P0 | 2026-03-27 | `pytest 17/17`, overlay values verified |
| M4.2-01 | API skeleton (health/config/predict endpoints) | DONE | P0 | 2026-03-27 | Added FastAPI app + endpoint tests |
| M4.2-02 | Unified app state + user interaction events | TODO | P1 | 2026-03-28 | Track UX behavior and actions |
| M4.2-03 | Replace proxy predictor with real trained model serving | DONE | P0 | 2026-03-27 | Artifact-based inference + strict fallback controls |
| M4.2-04 | Add API auth guard + role checks | DONE | P0 | 2026-03-27 | Added API key guard for config/predict routes |
| M4.2-05 | Add request event logging for user interactions | DONE | P1 | 2026-03-27 | Added JSONL event logger + platform hooks + tests |
| M4.2-06 | Add model metadata endpoint for clients | DONE | P1 | 2026-03-27 | Added `/model/brain-age/metadata` + endpoint tests |
| M4.3-01 | API role policy with user identity claims | DONE | P0 | 2026-03-27 | Added role checks via `X-User-Id` and `X-User-Role` |
| M4.3-02 | Event log aggregation/report utility | DONE | P1 | 2026-03-27 | Added `summarize_event_log` + `/events/summary` endpoint |
| M4.3-03 | API contract docs and usage examples | DONE | P1 | 2026-03-27 | Added `docs/api/API_CONTRACT.md` |
| M4.3-04 | Role claim source integration (real identity provider) | DONE | P0 | 2026-03-27 | Added configurable `identity.mode` with JWT HS256 claims |
| M4.3-05 | Event summary filters (time/source/type) | DONE | P1 | 2026-03-27 | Added query filters to `/events/summary` |
| M4.3-06 | Security audit log for denied API requests | DONE | P1 | 2026-03-27 | Added `api_auth_failed` and `api_role_forbidden` logs |
| M4.4-01 | Add OIDC/JWKS verification support | TODO | P0 | 2026-03-28 | Replace shared-secret JWT mode with provider keys |
| M4.4-02 | Log retention + rotation policy | DONE | P1 | 2026-03-27 | Added rotation utility + `scripts/rotate_logs.py` |
| M4.4-03 | Event summary time-bucket metrics | DONE | P1 | 2026-03-27 | Added `group_by` + `top_n` controls |
| M4.4-04 | API endpoint for log maintenance status | TODO | P2 | 2026-03-28 | Expose last rotation metadata |

## Immediate Next Actions
1. Add OIDC/JWKS verification support for identity claims.
2. Add pagination for raw event inspection endpoint.
3. Add endpoint for log maintenance/rotation status.
