from pathlib import Path

import pytest
import yaml

from src.data.utils import load_config


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _minimal_base_config() -> dict:
    return {
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "actigraphy_file": "data/raw/actigraphy.csv",
            "mri_file": "data/raw/mri.csv",
            "clinical_file": "data/raw/clinical.csv",
        },
        "output": {"figures_dir": "outputs/figures"},
        "sleep_features": {"features": ["sleep_efficiency"]},
        "causal_inference": {"ps_method": "super_learner"},
        "statistics": {"random_seed": 2026},
    }


def test_load_config_applies_environment_overlay(tmp_path):
    config_dir = tmp_path / "config"
    base_path = config_dir / "config.yaml"
    dev_path = config_dir / "dev.yaml"

    _write_yaml(base_path, _minimal_base_config())
    _write_yaml(
        dev_path,
        {
            "statistics": {"random_seed": 999},
            "feature_flags": {"enable_model_auto_selection": False},
        },
    )

    cfg = load_config(str(base_path), env="dev")
    assert cfg["statistics"]["random_seed"] == 999
    assert cfg["feature_flags"]["enable_model_auto_selection"] is False


def test_load_config_adds_default_feature_flags_when_missing(tmp_path):
    config_path = tmp_path / "config" / "config.yaml"
    _write_yaml(config_path, _minimal_base_config())

    cfg = load_config(str(config_path), env=None)
    assert "feature_flags" in cfg
    assert isinstance(cfg["feature_flags"], dict)


def test_load_config_raises_on_missing_required_sections(tmp_path):
    broken_path = tmp_path / "config" / "config.yaml"
    _write_yaml(broken_path, {"data": {"raw_dir": "data/raw"}})

    with pytest.raises(ValueError, match="Missing required config sections"):
        load_config(str(broken_path), env=None)


def test_load_config_raises_on_invalid_api_flag_type(tmp_path):
    config_path = tmp_path / "config" / "config.yaml"
    cfg = _minimal_base_config()
    cfg["api"] = {
        "brain_age_delta_artifact": "outputs/models/brain_age_delta_model.joblib",
        "allow_proxy_fallback": "yes",
    }
    _write_yaml(config_path, cfg)

    with pytest.raises(ValueError, match="api.allow_proxy_fallback must be a boolean"):
        load_config(str(config_path), env=None)


def test_load_config_raises_on_invalid_role_requirements_type(tmp_path):
    config_path = tmp_path / "config" / "config.yaml"
    cfg = _minimal_base_config()
    cfg["api"] = {
        "brain_age_delta_artifact": "outputs/models/brain_age_delta_model.joblib",
        "allow_proxy_fallback": True,
        "require_api_key": False,
        "enable_role_policy": True,
        "role_requirements": ["admin"],
    }
    _write_yaml(config_path, cfg)

    with pytest.raises(ValueError, match="api.role_requirements must be a dictionary"):
        load_config(str(config_path), env=None)
