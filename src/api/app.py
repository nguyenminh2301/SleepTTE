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
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from src.data.utils import load_config


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


def _enforce_api_key(cfg: dict, x_api_key: str | None) -> None:
    api_cfg = cfg.get("api", {})
    require_api_key = api_cfg.get("require_api_key", False)
    if not require_api_key:
        return

    expected_api_key = os.getenv("SLEEPTTE_API_KEY", api_cfg.get("api_key", ""))
    if not expected_api_key or x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key.")


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
        x_api_key: str | None = Header(default=None, alias="X-API-Key")
    ) -> dict:
        try:
            cfg = load_config()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load config: {exc}") from exc
        _enforce_api_key(cfg, x_api_key)

        return {
            "data_paths": cfg.get("data", {}),
            "brain_modeling": cfg.get("brain_modeling", {}),
            "feature_flags": cfg.get("feature_flags", {}),
            "api": cfg.get("api", {}),
        }

    @app.post("/predict/brain-age", response_model=BrainAgePredictionResponse)
    def predict_brain_age(
        payload: BrainAgePredictionRequest,
        x_api_key: str | None = Header(default=None, alias="X-API-Key")
    ) -> BrainAgePredictionResponse:
        cfg = load_config()
        _enforce_api_key(cfg, x_api_key)
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
        x_api_key: str | None = Header(default=None, alias="X-API-Key")
    ) -> dict:
        cfg = load_config()
        _enforce_api_key(cfg, x_api_key)

        artifact = _load_brain_age_artifact(cfg)
        if artifact is None:
            raise HTTPException(status_code=404, detail="Brain-age artifact not found.")

        return _artifact_metadata(artifact)

    return app


app = create_app()
