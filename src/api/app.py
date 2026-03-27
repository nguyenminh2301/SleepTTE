"""
FastAPI skeleton for SleepTTE.
Round 4.2 foundation endpoints:
- GET /health
- GET /config
- POST /predict/brain-age
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import os

import joblib
import numpy as np
import pandas as pd
import jwt
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from src.data.utils import load_config
from src.utils.event_summary import summarize_event_log
from src.utils.event_logger import log_event


class BrainAgePredictionRequest(BaseModel):
    sleep_efficiency: float = Field(..., ge=0, le=100)
    sleep_fragmentation_index: float = Field(..., ge=0)
    sleep_regularity_index: float = Field(..., ge=0, le=100)
    social_jet_lag: float = Field(..., ge=0)
    age: float = Field(..., ge=18, le=120)


class BrainAgePredictionResponse(BaseModel):
    predicted_brain_age_delta: float
    risk_level: Literal["low", "moderate", "high"]
    model_version: str


_ARTIFACT_CACHE: dict[str, dict] = {}


def _predict_brain_age_delta_proxy(payload: BrainAgePredictionRequest) -> float:
    """
    Proxy predictor for API skeleton.
    This is intentionally lightweight until model serving is integrated.
    """
    score = (
        0.08 * (85 - payload.sleep_efficiency)
        + 0.15 * payload.sleep_fragmentation_index
        + 0.06 * (75 - payload.sleep_regularity_index)
        + 0.30 * payload.social_jet_lag
        + 0.02 * (payload.age - 60)
    )
    return round(float(score), 3)


def _resolve_artifact_path(cfg: dict) -> Path:
    api_cfg = cfg.get("api", {})
    artifact = api_cfg.get(
        "brain_age_delta_artifact",
        "outputs/models/brain_age_delta_model.joblib"
    )
    return Path(artifact)


def _load_brain_age_artifact(cfg: dict) -> dict | None:
    artifact_path = _resolve_artifact_path(cfg)
    cache_key = str(artifact_path.resolve())

    if cache_key in _ARTIFACT_CACHE:
        return _ARTIFACT_CACHE[cache_key]

    if not artifact_path.exists():
        return None

    artifact = joblib.load(artifact_path)
    required_keys = ["model", "scaler", "feature_names", "feature_defaults"]
    missing = [k for k in required_keys if k not in artifact]
    if missing:
        raise ValueError(f"Invalid artifact, missing keys: {missing}")

    _ARTIFACT_CACHE[cache_key] = artifact
    return artifact


def _predict_brain_age_delta_from_artifact(
    payload: BrainAgePredictionRequest,
    artifact: dict
) -> float:
    feature_names = artifact["feature_names"]
    defaults = artifact.get("feature_defaults", {})

    feature_values = {name: float(defaults.get(name, 0.0)) for name in feature_names}
    overrides = {
        "sleep_efficiency": payload.sleep_efficiency,
        "sleep_fragmentation_index": payload.sleep_fragmentation_index,
        "sleep_regularity_index": payload.sleep_regularity_index,
        "social_jet_lag": payload.social_jet_lag,
        "age": payload.age,
    }
    for key, value in overrides.items():
        if key in feature_values:
            feature_values[key] = float(value)

    x = pd.DataFrame(
        [{name: feature_values[name] for name in feature_names}],
        columns=feature_names
    )
    x_scaled = artifact["scaler"].transform(x)
    prediction = artifact["model"].predict(x_scaled)
    return round(float(np.asarray(prediction)[0]), 3)


def _artifact_metadata(artifact: dict) -> dict:
    metrics = artifact.get("metrics", {})
    return {
        "biomarker": artifact.get("biomarker", "brain_age_delta"),
        "artifact_version": artifact.get("artifact_version", "v1"),
        "created_at_utc": artifact.get("created_at_utc"),
        "feature_names": artifact.get("feature_names", []),
        "selected_model": metrics.get("selected_model"),
        "cv_mae": metrics.get("cv_mae"),
        "cv_r2": metrics.get("cv_r2"),
    }


def _risk_level(delta: float) -> Literal["low", "moderate", "high"]:
    if delta < 1:
        return "low"
    if delta < 3:
        return "moderate"
    return "high"


def _enforce_api_key(
    cfg: dict,
    x_api_key: str | None,
    endpoint_key: str,
    x_user_id: str | None,
    x_user_role: str | None,
) -> None:
    api_cfg = cfg.get("api", {})
    require_api_key = api_cfg.get("require_api_key", False)
    if not require_api_key:
        return

    expected_api_key = os.getenv("SLEEPTTE_API_KEY", api_cfg.get("api_key", ""))
    if not expected_api_key or x_api_key != expected_api_key:
        _log_security_event(
            cfg=cfg,
            event_type="api_auth_failed",
            endpoint_key=endpoint_key,
            user_id=x_user_id,
            user_role=x_user_role,
            reason="invalid_api_key",
        )
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key.")


def _resolve_identity_claims(
    cfg: dict,
    x_user_id: str | None,
    x_user_role: str | None,
    authorization: str | None,
) -> tuple[str | None, str | None]:
    identity_cfg = cfg.get("identity", {})
    mode = identity_cfg.get("mode", "header")
    if mode == "header":
        return x_user_id, x_user_role

    if mode == "jwt_hs256":
        if not authorization or not authorization.lower().startswith("bearer "):
            return None, None
        token = authorization.split(" ", 1)[1].strip()
        secret = os.getenv("SLEEPTTE_JWT_SECRET", identity_cfg.get("jwt_hs256_secret", ""))
        if not secret:
            return None, None
        try:
            decoded = jwt.decode(token, secret, algorithms=["HS256"])
        except Exception:
            return None, None

        user_id_claim = identity_cfg.get("jwt_user_id_claim", "sub")
        role_claim = identity_cfg.get("jwt_role_claim", "role")
        user_id_val = decoded.get(user_id_claim)
        role_val = decoded.get(role_claim)
        return (
            str(user_id_val) if user_id_val is not None else None,
            str(role_val) if role_val is not None else None,
        )

    return x_user_id, x_user_role


def _enforce_role_policy(
    cfg: dict,
    endpoint_key: str,
    x_user_id: str | None,
    x_user_role: str | None
) -> None:
    api_cfg = cfg.get("api", {})
    if not api_cfg.get("enable_role_policy", False):
        return

    role_requirements = api_cfg.get("role_requirements", {})
    allowed_roles = role_requirements.get(endpoint_key, [])
    if not allowed_roles:
        return

    if not x_user_id or not x_user_role:
        _log_security_event(
            cfg=cfg,
            event_type="api_auth_failed",
            endpoint_key=endpoint_key,
            user_id=x_user_id,
            user_role=x_user_role,
            reason="missing_identity_claims",
        )
        raise HTTPException(status_code=401, detail="Unauthorized: missing identity claims.")
    if x_user_role not in allowed_roles:
        _log_security_event(
            cfg=cfg,
            event_type="api_role_forbidden",
            endpoint_key=endpoint_key,
            user_id=x_user_id,
            user_role=x_user_role,
            reason="role_not_allowed",
        )
        raise HTTPException(status_code=403, detail="Forbidden: role is not allowed for this endpoint.")


def _log_security_event(
    cfg: dict,
    event_type: str,
    endpoint_key: str,
    user_id: str | None,
    user_role: str | None,
    reason: str,
) -> None:
    log_path = cfg.get("api", {}).get("security_event_log_path", "logs/security_events.log")
    log_event(
        event_type=event_type,
        source="api",
        user_id=user_id,
        payload={
            "endpoint": endpoint_key,
            "user_role": user_role,
            "reason": reason,
        },
        log_path=log_path,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="SleepTTE API",
        version="0.1.0",
        description="API skeleton for SleepTTE platform",
    )

    @app.get("/health")
    def health() -> dict:
        cfg = load_config()
        artifact_exists = _resolve_artifact_path(cfg).exists()
        return {
            "status": "ok",
            "service": "sleeptte-api",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "brain_age_model_artifact_loaded": artifact_exists,
        }

    @app.get("/config")
    def get_config_summary(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        x_user_role: str | None = Header(default=None, alias="X-User-Role"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        try:
            cfg = load_config()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load config: {exc}") from exc
        resolved_user_id, resolved_user_role = _resolve_identity_claims(
            cfg, x_user_id, x_user_role, authorization
        )
        _enforce_api_key(
            cfg,
            x_api_key,
            endpoint_key="config",
            x_user_id=resolved_user_id,
            x_user_role=resolved_user_role
        )
        _enforce_role_policy(cfg, "config", resolved_user_id, resolved_user_role)

        return {
            "data_paths": cfg.get("data", {}),
            "brain_modeling": cfg.get("brain_modeling", {}),
            "feature_flags": cfg.get("feature_flags", {}),
            "api": cfg.get("api", {}),
        }

    @app.post("/predict/brain-age", response_model=BrainAgePredictionResponse)
    def predict_brain_age(
        payload: BrainAgePredictionRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        x_user_role: str | None = Header(default=None, alias="X-User-Role"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> BrainAgePredictionResponse:
        cfg = load_config()
        resolved_user_id, resolved_user_role = _resolve_identity_claims(
            cfg, x_user_id, x_user_role, authorization
        )
        _enforce_api_key(
            cfg,
            x_api_key,
            endpoint_key="predict_brain_age",
            x_user_id=resolved_user_id,
            x_user_role=resolved_user_role,
        )
        _enforce_role_policy(cfg, "predict_brain_age", resolved_user_id, resolved_user_role)
        api_cfg = cfg.get("api", {})
        allow_proxy_fallback = api_cfg.get("allow_proxy_fallback", True)

        artifact = _load_brain_age_artifact(cfg)
        if artifact is not None:
            delta = _predict_brain_age_delta_from_artifact(payload, artifact)
            model_version = f"artifact-{artifact.get('artifact_version', 'v1')}"
        elif allow_proxy_fallback:
            delta = _predict_brain_age_delta_proxy(payload)
            model_version = "proxy-fallback-v0.2"
        else:
            raise HTTPException(
                status_code=503,
                detail="Model artifact unavailable and proxy fallback disabled."
            )

        return BrainAgePredictionResponse(
            predicted_brain_age_delta=delta,
            risk_level=_risk_level(delta),
            model_version=model_version,
        )

    @app.get("/model/brain-age/metadata")
    def get_brain_age_model_metadata(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        x_user_role: str | None = Header(default=None, alias="X-User-Role"),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        cfg = load_config()
        resolved_user_id, resolved_user_role = _resolve_identity_claims(
            cfg, x_user_id, x_user_role, authorization
        )
        _enforce_api_key(
            cfg,
            x_api_key,
            endpoint_key="model_metadata",
            x_user_id=resolved_user_id,
            x_user_role=resolved_user_role
        )
        _enforce_role_policy(cfg, "model_metadata", resolved_user_id, resolved_user_role)

        artifact = _load_brain_age_artifact(cfg)
        if artifact is None:
            raise HTTPException(status_code=404, detail="Brain-age artifact not found.")

        return _artifact_metadata(artifact)

    @app.get("/events/summary")
    def get_event_summary(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        x_user_role: str | None = Header(default=None, alias="X-User-Role"),
        authorization: str | None = Header(default=None, alias="Authorization"),
        start_time_utc: str | None = None,
        end_time_utc: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        group_by: str | None = None,
        top_n: int | None = None,
    ) -> dict:
        cfg = load_config()
        resolved_user_id, resolved_user_role = _resolve_identity_claims(
            cfg, x_user_id, x_user_role, authorization
        )
        _enforce_api_key(
            cfg,
            x_api_key,
            endpoint_key="events_summary",
            x_user_id=resolved_user_id,
            x_user_role=resolved_user_role
        )
        _enforce_role_policy(cfg, "events_summary", resolved_user_id, resolved_user_role)

        log_path = cfg.get("api", {}).get("event_log_path", "logs/events.log")
        return summarize_event_log(
            log_path=log_path,
            start_time_utc=start_time_utc,
            end_time_utc=end_time_utc,
            event_type=event_type,
            source=source,
            group_by=group_by,
            top_n=top_n,
        )

    return app


app = create_app()
