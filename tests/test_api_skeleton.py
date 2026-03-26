from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import StandardScaler

import src.api.app as api_module
from src.api.app import create_app


client = TestClient(create_app())


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "sleeptte-api"


def test_config_endpoint_returns_core_sections():
    response = client.get("/config")
    assert response.status_code == 200
    payload = response.json()
    assert "data_paths" in payload
    assert "brain_modeling" in payload
    assert "feature_flags" in payload


def test_predict_brain_age_endpoint_returns_prediction_and_risk():
    response = client.post(
        "/predict/brain-age",
        json={
            "sleep_efficiency": 78.0,
            "sleep_fragmentation_index": 12.0,
            "sleep_regularity_index": 62.0,
            "social_jet_lag": 2.5,
            "age": 68.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "predicted_brain_age_delta" in payload
    assert payload["risk_level"] in {"low", "moderate", "high"}
    assert payload["model_version"] in {"proxy-fallback-v0.2", "artifact-v1"}


def test_predict_brain_age_uses_artifact_when_available(tmp_path, monkeypatch):
    artifact_path = tmp_path / "brain_age_delta_model.joblib"

    feature_names = [
        "sleep_efficiency",
        "sleep_fragmentation_index",
        "sleep_regularity_index",
        "social_jet_lag",
        "age",
    ]
    x_train = pd.DataFrame(
        [[80.0, 12.0, 60.0, 2.0, 70.0]],
        columns=feature_names
    )
    y_train = np.array([2.5], dtype=float)
    scaler = StandardScaler().fit(x_train)
    model = DummyRegressor(strategy="constant", constant=2.5)
    model.fit(scaler.transform(x_train), y_train)

    joblib.dump(
        {
            "model": model,
            "scaler": scaler,
            "feature_names": feature_names,
            "feature_defaults": {name: 0.0 for name in feature_names},
            "artifact_version": "v1",
        },
        artifact_path,
    )

    def _mock_load_config(*args, **kwargs):
        return {
            "data": {"raw_dir": "data/raw", "processed_dir": "data/processed", "actigraphy_file": "", "mri_file": "", "clinical_file": ""},
            "output": {},
            "sleep_features": {"features": []},
            "causal_inference": {},
            "statistics": {},
            "brain_modeling": {},
            "feature_flags": {},
            "api": {
                "brain_age_delta_artifact": str(artifact_path),
                "allow_proxy_fallback": False,
            },
        }

    monkeypatch.setattr(api_module, "load_config", _mock_load_config)
    api_module._ARTIFACT_CACHE.clear()
    test_client = TestClient(create_app())

    response = test_client.post(
        "/predict/brain-age",
        json={
            "sleep_efficiency": 78.0,
            "sleep_fragmentation_index": 12.0,
            "sleep_regularity_index": 62.0,
            "social_jet_lag": 2.5,
            "age": 68.0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_version"] == "artifact-v1"
    assert abs(payload["predicted_brain_age_delta"] - 2.5) < 1e-6


def test_predict_brain_age_returns_503_when_artifact_missing_and_no_fallback(monkeypatch):
    missing_path = Path("outputs/models/does_not_exist.joblib")

    def _mock_load_config(*args, **kwargs):
        return {
            "data": {"raw_dir": "data/raw", "processed_dir": "data/processed", "actigraphy_file": "", "mri_file": "", "clinical_file": ""},
            "output": {},
            "sleep_features": {"features": []},
            "causal_inference": {},
            "statistics": {},
            "brain_modeling": {},
            "feature_flags": {},
            "api": {
                "brain_age_delta_artifact": str(missing_path),
                "allow_proxy_fallback": False,
            },
        }

    monkeypatch.setattr(api_module, "load_config", _mock_load_config)
    api_module._ARTIFACT_CACHE.clear()
    test_client = TestClient(create_app())

    response = test_client.post(
        "/predict/brain-age",
        json={
            "sleep_efficiency": 78.0,
            "sleep_fragmentation_index": 12.0,
            "sleep_regularity_index": 62.0,
            "social_jet_lag": 2.5,
            "age": 68.0,
        },
    )
    assert response.status_code == 503


def test_predict_requires_api_key_when_enabled(monkeypatch):
    def _mock_load_config(*args, **kwargs):
        return {
            "data": {"raw_dir": "data/raw", "processed_dir": "data/processed", "actigraphy_file": "", "mri_file": "", "clinical_file": ""},
            "output": {},
            "sleep_features": {"features": []},
            "causal_inference": {},
            "statistics": {},
            "brain_modeling": {},
            "feature_flags": {},
            "api": {
                "brain_age_delta_artifact": "outputs/models/missing.joblib",
                "allow_proxy_fallback": True,
                "require_api_key": True,
                "api_key": "secret-key",
            },
        }

    monkeypatch.setattr(api_module, "load_config", _mock_load_config)
    api_module._ARTIFACT_CACHE.clear()
    test_client = TestClient(create_app())

    response = test_client.post(
        "/predict/brain-age",
        json={
            "sleep_efficiency": 78.0,
            "sleep_fragmentation_index": 12.0,
            "sleep_regularity_index": 62.0,
            "social_jet_lag": 2.5,
            "age": 68.0,
        },
    )
    assert response.status_code == 401


def test_predict_accepts_api_key_when_enabled(monkeypatch):
    def _mock_load_config(*args, **kwargs):
        return {
            "data": {"raw_dir": "data/raw", "processed_dir": "data/processed", "actigraphy_file": "", "mri_file": "", "clinical_file": ""},
            "output": {},
            "sleep_features": {"features": []},
            "causal_inference": {},
            "statistics": {},
            "brain_modeling": {},
            "feature_flags": {},
            "api": {
                "brain_age_delta_artifact": "outputs/models/missing.joblib",
                "allow_proxy_fallback": True,
                "require_api_key": True,
                "api_key": "secret-key",
            },
        }

    monkeypatch.setattr(api_module, "load_config", _mock_load_config)
    api_module._ARTIFACT_CACHE.clear()
    test_client = TestClient(create_app())

    response = test_client.post(
        "/predict/brain-age",
        json={
            "sleep_efficiency": 78.0,
            "sleep_fragmentation_index": 12.0,
            "sleep_regularity_index": 62.0,
            "social_jet_lag": 2.5,
            "age": 68.0,
        },
        headers={"X-API-Key": "secret-key"},
    )
    assert response.status_code == 200


def test_model_metadata_returns_404_when_artifact_missing(monkeypatch):
    def _mock_load_config(*args, **kwargs):
        return {
            "data": {"raw_dir": "data/raw", "processed_dir": "data/processed", "actigraphy_file": "", "mri_file": "", "clinical_file": ""},
            "output": {},
            "sleep_features": {"features": []},
            "causal_inference": {},
            "statistics": {},
            "brain_modeling": {},
            "feature_flags": {},
            "api": {
                "brain_age_delta_artifact": "outputs/models/missing.joblib",
                "allow_proxy_fallback": True,
                "require_api_key": False,
                "api_key": "secret-key",
            },
        }

    monkeypatch.setattr(api_module, "load_config", _mock_load_config)
    api_module._ARTIFACT_CACHE.clear()
    test_client = TestClient(create_app())

    response = test_client.get("/model/brain-age/metadata")
    assert response.status_code == 404


def test_model_metadata_returns_artifact_details(tmp_path, monkeypatch):
    artifact_path = tmp_path / "brain_age_delta_model.joblib"
    feature_names = ["sleep_efficiency", "sleep_fragmentation_index"]
    x_train = pd.DataFrame([[80.0, 12.0]], columns=feature_names)
    y_train = np.array([2.0], dtype=float)
    scaler = StandardScaler().fit(x_train)
    model = DummyRegressor(strategy="constant", constant=2.0)
    model.fit(scaler.transform(x_train), y_train)

    joblib.dump(
        {
            "biomarker": "brain_age_delta",
            "model": model,
            "scaler": scaler,
            "feature_names": feature_names,
            "feature_defaults": {name: 0.0 for name in feature_names},
            "artifact_version": "v1",
            "created_at_utc": "2026-03-27T00:00:00+00:00",
            "metrics": {"selected_model": "ridge", "cv_mae": 1.2, "cv_r2": 0.1},
        },
        artifact_path,
    )

    def _mock_load_config(*args, **kwargs):
        return {
            "data": {"raw_dir": "data/raw", "processed_dir": "data/processed", "actigraphy_file": "", "mri_file": "", "clinical_file": ""},
            "output": {},
            "sleep_features": {"features": []},
            "causal_inference": {},
            "statistics": {},
            "brain_modeling": {},
            "feature_flags": {},
            "api": {
                "brain_age_delta_artifact": str(artifact_path),
                "allow_proxy_fallback": False,
                "require_api_key": False,
                "api_key": "secret-key",
            },
        }

    monkeypatch.setattr(api_module, "load_config", _mock_load_config)
    api_module._ARTIFACT_CACHE.clear()
    test_client = TestClient(create_app())

    response = test_client.get("/model/brain-age/metadata")
    assert response.status_code == 200
    payload = response.json()
    assert payload["biomarker"] == "brain_age_delta"
    assert payload["artifact_version"] == "v1"
    assert payload["selected_model"] == "ridge"
