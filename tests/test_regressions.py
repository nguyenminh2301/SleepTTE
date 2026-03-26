import numpy as np
import pandas as pd
import joblib
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import StandardScaler

from src.features.sleep_features import detect_sleep_wake
from src.models.brain_age_model import (
    prepare_feature_matrix,
    build_brain_aging_model,
    save_model_artifact,
)
from src.utils.stats import estimate_propensity_scores


def test_detect_sleep_wake_marks_low_activity_as_sleep():
    activity_counts = np.full(60, 2.0)
    sleep_wake = detect_sleep_wake(activity_counts, threshold=0.04)
    assert sleep_wake.sum() > 0


def test_prepare_feature_matrix_fills_all_nan_columns():
    X = pd.DataFrame(
        {
            "sleep_efficiency": [80.0, 82.5, np.nan],
            "sleep_onset_latency": [np.nan, np.nan, np.nan],
        }
    )
    prepared = prepare_feature_matrix(X)
    assert not prepared.isna().any().any()


def test_build_brain_aging_model_reports_oof_metrics():
    np.random.seed(2026)
    X = pd.DataFrame(
        {
            "sleep_efficiency": np.random.normal(85, 4, 40),
            "sleep_fragmentation_index": np.random.normal(5, 1.5, 40),
            "social_jet_lag": np.random.uniform(0, 3, 40),
        }
    )
    y = 0.2 * X["sleep_fragmentation_index"] - 0.1 * X["sleep_efficiency"] + np.random.normal(0, 1, 40)

    _, _, predictions, metrics, leaderboard = build_brain_aging_model(X, y, model_type="auto")

    assert len(predictions) == len(y)
    assert "cv_mae" in metrics
    assert "cv_r2" in metrics
    assert "train_mae" in metrics
    assert "train_r2" in metrics
    assert "selected_model" in metrics
    assert not leaderboard.empty
    assert "model" in leaderboard.columns


def test_build_brain_aging_model_respects_candidate_models_config():
    np.random.seed(2026)
    X = pd.DataFrame(
        {
            "sleep_efficiency": np.random.normal(85, 4, 36),
            "sleep_fragmentation_index": np.random.normal(5, 1.5, 36),
            "social_jet_lag": np.random.uniform(0, 3, 36),
        }
    )
    y = 0.25 * X["sleep_fragmentation_index"] - 0.1 * X["sleep_efficiency"] + np.random.normal(0, 1, 36)

    model_config = {
        "candidate_models": ["dummy_mean", "ridge"],
        "cv_folds": 3,
        "random_seed": 2026,
        "n_jobs": 1,
    }

    _, _, _, metrics, leaderboard = build_brain_aging_model(
        X, y, model_type="auto", model_config=model_config
    )

    assert set(leaderboard["model"]) <= {"dummy_mean", "ridge"}
    assert metrics["selected_model"] in {"dummy_mean", "ridge"}


def test_super_learner_propensity_scores_return_valid_probabilities():
    np.random.seed(2026)
    X = pd.DataFrame(
        {
            "age": np.random.normal(65, 5, 30),
            "bmi": np.random.normal(25, 2, 30),
            "sleep_efficiency": np.random.normal(82, 5, 30),
        }
    )
    treatment = pd.Series([0] * 18 + [1] * 12)

    ps = estimate_propensity_scores(
        X,
        treatment,
        method="super_learner",
        base_learners=["logistic", "neural_network"],
        verbose=False,
    )

    assert len(ps) == len(treatment)
    assert np.all(ps >= 0.01)
    assert np.all(ps <= 0.99)


def test_save_model_artifact_writes_expected_payload(tmp_path):
    feature_names = ["sleep_efficiency", "sleep_fragmentation_index"]
    x_train = np.array([[80.0, 10.0], [82.0, 8.0]], dtype=float)
    y_train = np.array([1.2, 0.8], dtype=float)

    scaler = StandardScaler().fit(x_train)
    model = DummyRegressor(strategy="mean")
    model.fit(scaler.transform(x_train), y_train)

    artifact_path = save_model_artifact(
        biomarker="brain_age_delta",
        model=model,
        scaler=scaler,
        feature_names=feature_names,
        feature_defaults={"sleep_efficiency": 81.0, "sleep_fragmentation_index": 9.0},
        metrics={"cv_mae": 1.0},
        output_dir=str(tmp_path),
    )
    loaded = joblib.load(artifact_path)

    assert loaded["biomarker"] == "brain_age_delta"
    assert loaded["artifact_version"] == "v1"
    assert loaded["feature_names"] == feature_names
