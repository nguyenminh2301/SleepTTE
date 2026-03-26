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
| M4.3-01 | API role policy with user identity claims | TODO | P0 | 2026-03-28 | Move from single API key to role-based checks |
| M4.3-02 | Event log aggregation/report utility | TODO | P1 | 2026-03-28 | Summarize usage patterns from `logs/events.log` |

## Immediate Next Actions
1. Add role policy with user identity claims.
2. Add event aggregation/report utility for `logs/events.log`.
3. Start API contract docs (OpenAPI usage + examples).
