"""
Demo dataset helpers for Streamlit apps.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_demo_sleep_features(n_patients: int = 20, seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    participant_ids = [f"P{i:04d}" for i in range(1, n_patients + 1)]

    sleep_eff = np.clip(rng.normal(83, 6, n_patients), 60, 98)
    frag = np.clip(rng.normal(12, 5, n_patients), 2, 30)
    regularity = np.clip(rng.normal(72, 12, n_patients), 35, 98)
    social_jet_lag = np.clip(rng.normal(1.8, 0.9, n_patients), 0, 5)
    total_sleep_time = np.clip(rng.normal(410, 55, n_patients), 280, 560)

    df = pd.DataFrame(
        {
            "participant_id": participant_ids,
            "total_sleep_time": total_sleep_time,
            "sleep_efficiency": sleep_eff,
            "sleep_onset_latency": np.clip(rng.normal(22, 10, n_patients), 5, 60),
            "wake_after_sleep_onset": np.clip(rng.normal(45, 20, n_patients), 5, 120),
            "number_of_awakenings": np.clip(rng.normal(4, 2, n_patients), 0, 12).round(),
            "sleep_fragmentation_index": frag,
            "interdaily_stability": np.clip(rng.normal(0.62, 0.12, n_patients), 0.15, 0.95),
            "intradaily_variability": np.clip(rng.normal(0.85, 0.25, n_patients), 0.2, 2.0),
            "relative_amplitude": np.clip(rng.normal(0.72, 0.12, n_patients), 0.2, 0.95),
            "acrophase": rng.integers(11, 18, n_patients),
            "sleep_regularity_index": regularity,
            "social_jet_lag": social_jet_lag,
        }
    )
    return df


def generate_demo_clinical(n_patients: int = 20, seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    return pd.DataFrame(
        {
            "participant_id": [f"P{i:04d}" for i in range(1, n_patients + 1)],
            "age": np.clip(rng.normal(68, 7, n_patients), 50, 85),
            "sex": rng.choice(["M", "F"], size=n_patients),
            "education_years": np.clip(rng.normal(14, 3, n_patients), 8, 20),
        }
    )


def generate_demo_mri(n_patients: int = 20, seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 2)
    return pd.DataFrame(
        {
            "participant_id": [f"P{i:04d}" for i in range(1, n_patients + 1)],
            "brain_age_delta": np.clip(rng.normal(1.2, 2.8, n_patients), -5, 10),
            "hippocampal_volume": np.clip(rng.normal(6900, 650, n_patients), 4500, 9000),
        }
    )
