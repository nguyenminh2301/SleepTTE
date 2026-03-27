"""
Data utility functions for TTE2026_sleep project
Handles data loading, preprocessing, and validation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import os
from typing import Dict, List, Tuple, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge `override` into `base`."""
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file must contain a mapping: {path}")
    return data


def validate_config(config: Dict[str, Any]) -> None:
    """Fail-fast validation for required configuration keys."""
    required_top_level = [
        "data",
        "output",
        "sleep_features",
        "causal_inference",
        "statistics",
    ]
    missing = [k for k in required_top_level if k not in config]
    if missing:
        raise ValueError(f"Missing required config sections: {missing}")

    required_data_keys = [
        "raw_dir",
        "processed_dir",
        "actigraphy_file",
        "mri_file",
        "clinical_file",
    ]
    missing_data = [k for k in required_data_keys if k not in config["data"]]
    if missing_data:
        raise ValueError(f"Missing required data config keys: {missing_data}")

    if "features" not in config["sleep_features"] or not isinstance(config["sleep_features"]["features"], list):
        raise ValueError("sleep_features.features must be a non-empty list")

    if "brain_modeling" in config:
        bm = config["brain_modeling"]
        if "candidate_models" in bm and not isinstance(bm["candidate_models"], list):
            raise ValueError("brain_modeling.candidate_models must be a list")
        if "cv_folds" in bm and int(bm["cv_folds"]) < 2:
            raise ValueError("brain_modeling.cv_folds must be >= 2")

    if "api" in config:
        api = config["api"]
        if "brain_age_delta_artifact" in api and not isinstance(api["brain_age_delta_artifact"], str):
            raise ValueError("api.brain_age_delta_artifact must be a string path")
        if "allow_proxy_fallback" in api and not isinstance(api["allow_proxy_fallback"], bool):
            raise ValueError("api.allow_proxy_fallback must be a boolean")
        if "require_api_key" in api and not isinstance(api["require_api_key"], bool):
            raise ValueError("api.require_api_key must be a boolean")
        if "api_key" in api and not isinstance(api["api_key"], str):
            raise ValueError("api.api_key must be a string")
        if "enable_role_policy" in api and not isinstance(api["enable_role_policy"], bool):
            raise ValueError("api.enable_role_policy must be a boolean")
        if "event_log_path" in api and not isinstance(api["event_log_path"], str):
            raise ValueError("api.event_log_path must be a string path")
        if "security_event_log_path" in api and not isinstance(api["security_event_log_path"], str):
            raise ValueError("api.security_event_log_path must be a string path")
        if "role_requirements" in api and not isinstance(api["role_requirements"], dict):
            raise ValueError("api.role_requirements must be a dictionary")

    if "identity" in config:
        identity = config["identity"]
        if "mode" in identity and identity["mode"] not in ["header", "jwt_hs256"]:
            raise ValueError("identity.mode must be one of: header, jwt_hs256")
        if "jwt_hs256_secret" in identity and not isinstance(identity["jwt_hs256_secret"], str):
            raise ValueError("identity.jwt_hs256_secret must be a string")
        if "jwt_user_id_claim" in identity and not isinstance(identity["jwt_user_id_claim"], str):
            raise ValueError("identity.jwt_user_id_claim must be a string")
        if "jwt_role_claim" in identity and not isinstance(identity["jwt_role_claim"], str):
            raise ValueError("identity.jwt_role_claim must be a string")

    if "operations" in config:
        ops = config["operations"]
        if "log_rotation_max_bytes" in ops and int(ops["log_rotation_max_bytes"]) <= 0:
            raise ValueError("operations.log_rotation_max_bytes must be > 0")
        if "log_rotation_backup_count" in ops and int(ops["log_rotation_backup_count"]) < 1:
            raise ValueError("operations.log_rotation_backup_count must be >= 1")

    # Always ensure feature_flags exists for forward-compatible toggles
    if "feature_flags" not in config or not isinstance(config["feature_flags"], dict):
        config["feature_flags"] = {}


def load_config(
    config_path: str = "config/config.yaml",
    env: Optional[str] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Load configuration with optional environment overlay.

    Resolution order:
    1) base file: `config_path`
    2) overlay file (if exists): `<config_dir>/<env>.yaml`
       - `env` is function arg or `SLEEPTTE_ENV` environment variable
    """
    base_path = Path(config_path)
    if not base_path.exists():
        raise FileNotFoundError(f"Config file not found: {base_path}")

    config = _load_yaml_file(base_path)

    resolved_env = env or os.getenv("SLEEPTTE_ENV", "").strip()
    if resolved_env:
        env_path = base_path.parent / f"{resolved_env}.yaml"
        if env_path.exists():
            logger.info("Applying config overlay for env=%s from %s", resolved_env, env_path)
            env_cfg = _load_yaml_file(env_path)
            config = _deep_merge(config, env_cfg)
        else:
            logger.info(
                "No overlay file found for env=%s at %s. Using base config only.",
                resolved_env,
                env_path
            )

    if validate:
        validate_config(config)

    return config


def load_actigraphy_data(file_path: str) -> pd.DataFrame:
    """
    Load actigraphy data
    
    Expected columns:
    - participant_id: Unique identifier
    - timestamp: DateTime of measurement
    - activity_counts: Activity counts per epoch
    - sleep_wake: Sleep/wake classification (if available)
    - wear_time: Whether device was worn
    """
    logger.info(f"Loading actigraphy data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Validate required columns
    required_cols = ['participant_id', 'timestamp', 'activity_counts']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} actigraphy records for {df['participant_id'].nunique()} participants")
    return df


def load_biomarker_data(file_path: str, biomarker_type: str) -> pd.DataFrame:
    """
    Load biomarker data (MRI, PET, plasma, MEG)
    
    Expected columns:
    - participant_id: Unique identifier
    - visit_date: Date of assessment
    - [biomarker-specific columns]
    """
    logger.info(f"Loading {biomarker_type} biomarker data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Validate participant_id exists
    if 'participant_id' not in df.columns:
        raise ValueError("Missing required column: participant_id")
    
    logger.info(f"Loaded {biomarker_type} data for {df['participant_id'].nunique()} participants")
    return df


def load_clinical_data(file_path: str) -> pd.DataFrame:
    """
    Load clinical and demographic data
    
    Expected columns:
    - participant_id: Unique identifier
    - age: Age at baseline
    - sex: Biological sex (M/F)
    - education_years: Years of education
    - apoe4_status: APOE4 carrier status (0/1/2)
    - cognitive_status: CU/MCI/Dementia
    """
    logger.info(f"Loading clinical data from {file_path}")
    df = pd.read_csv(file_path)
    
    required_cols = ['participant_id', 'age', 'sex']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded clinical data for {df['participant_id'].nunique()} participants")
    return df


def merge_multimodal_data(
    actigraphy: pd.DataFrame,
    mri: pd.DataFrame,
    pet: Optional[pd.DataFrame] = None,
    plasma: Optional[pd.DataFrame] = None,
    meg: Optional[pd.DataFrame] = None,
    clinical: Optional[pd.DataFrame] = None,
    time_window_days: int = 90
) -> pd.DataFrame:
    """
    Merge multimodal data with temporal alignment
    
    Args:
        actigraphy: Actigraphy data (aggregated to participant level)
        mri: MRI biomarker data
        pet: PET biomarker data (optional)
        plasma: Plasma biomarker data (optional)
        meg: MEG data (optional)
        clinical: Clinical/demographic data (optional)
        time_window_days: Maximum days between assessments for matching
    
    Returns:
        Merged dataframe with all modalities
    """
    logger.info("Merging multimodal data...")
    
    # Start with MRI as anchor (most common biomarker)
    merged = mri.copy()
    
    # Merge clinical data (no temporal constraint)
    if clinical is not None:
        merged = merged.merge(clinical, on='participant_id', how='left', suffixes=('', '_clinical'))
    
    # Merge other biomarkers with temporal alignment
    for df, name in [(pet, 'PET'), (plasma, 'Plasma'), (meg, 'MEG')]:
        if df is not None:
            # Implement temporal matching logic here
            # For now, simple merge on participant_id
            merged = merged.merge(df, on='participant_id', how='left', suffixes=('', f'_{name.lower()}'))
    
    # Merge actigraphy (aggregated features)
    if 'participant_id' in actigraphy.columns:
        merged = merged.merge(actigraphy, on='participant_id', how='left', suffixes=('', '_actigraphy'))
    
    logger.info(f"Merged data contains {len(merged)} records for {merged['participant_id'].nunique()} participants")
    return merged


def quality_control_actigraphy(
    df: pd.DataFrame,
    min_wear_time_hours: float = 20.0,
    min_valid_days: int = 5
) -> pd.DataFrame:
    """
    Apply quality control filters to actigraphy data
    
    Args:
        df: Actigraphy dataframe
        min_wear_time_hours: Minimum wear time per day
        min_valid_days: Minimum valid days required
    
    Returns:
        Filtered dataframe with quality flags
    """
    logger.info("Applying quality control to actigraphy data...")
    
    # Calculate daily wear time
    df['date'] = df['timestamp'].dt.date
    daily_wear = df.groupby(['participant_id', 'date']).agg({
        'wear_time': 'sum' if 'wear_time' in df.columns else 'count'
    }).reset_index()
    
    # Assuming epochs are 1 minute
    daily_wear['wear_hours'] = daily_wear['wear_time'] / 60
    
    # Flag valid days
    daily_wear['valid_day'] = daily_wear['wear_hours'] >= min_wear_time_hours
    
    # Count valid days per participant
    valid_days_count = daily_wear.groupby('participant_id')['valid_day'].sum().reset_index()
    valid_days_count.columns = ['participant_id', 'n_valid_days']
    
    # Filter participants with sufficient valid days
    valid_participants = valid_days_count[valid_days_count['n_valid_days'] >= min_valid_days]['participant_id']
    
    df_filtered = df[df['participant_id'].isin(valid_participants)].copy()
    
    logger.info(f"Quality control: {len(valid_participants)}/{df['participant_id'].nunique()} participants retained")
    return df_filtered


def handle_missing_data(
    df: pd.DataFrame,
    strategy: str = 'drop',
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Handle missing data
    
    Args:
        df: Input dataframe
        strategy: 'drop', 'impute_mean', 'impute_median', 'mice'
        threshold: Maximum proportion of missing values allowed per column
    
    Returns:
        Dataframe with missing data handled
    """
    logger.info(f"Handling missing data with strategy: {strategy}")
    
    # Calculate missing proportions
    missing_props = df.isnull().sum() / len(df)
    
    # Drop columns with too much missing data
    cols_to_drop = missing_props[missing_props > threshold].index.tolist()
    if cols_to_drop:
        logger.warning(f"Dropping {len(cols_to_drop)} columns with >{threshold*100}% missing: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
    
    if strategy == 'drop':
        df = df.dropna()
    elif strategy == 'impute_mean':
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
    elif strategy == 'impute_median':
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    elif strategy == 'mice':
        # Implement MICE imputation if needed
        logger.warning("MICE imputation not yet implemented, using median imputation")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    
    logger.info(f"After handling missing data: {len(df)} records retained")
    return df


def create_analysis_dataset(config: Dict) -> pd.DataFrame:
    """
    Create complete analysis dataset by loading and merging all data sources
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Analysis-ready dataframe
    """
    logger.info("Creating analysis dataset...")
    
    # Load all data sources
    clinical = load_clinical_data(config['data']['clinical_file'])
    
    # Load biomarkers
    mri = load_biomarker_data(config['data']['mri_file'], 'MRI')
    
    # Optional biomarkers
    try:
        pet = load_biomarker_data(config['data']['pet_file'], 'PET')
    except FileNotFoundError:
        logger.warning("PET data not found, proceeding without it")
        pet = None
    
    try:
        plasma = load_biomarker_data(config['data']['plasma_file'], 'Plasma')
    except FileNotFoundError:
        logger.warning("Plasma data not found, proceeding without it")
        plasma = None
    
    try:
        meg = load_biomarker_data(config['data']['meg_file'], 'MEG')
    except FileNotFoundError:
        logger.warning("MEG data not found, proceeding without it")
        meg = None
    
    # Actigraphy will be processed separately and aggregated
    # For now, assume we have aggregated sleep features
    
    # Merge all data
    analysis_df = merge_multimodal_data(
        actigraphy=pd.DataFrame(),  # Placeholder
        mri=mri,
        pet=pet,
        plasma=plasma,
        meg=meg,
        clinical=clinical
    )
    
    # Handle missing data
    analysis_df = handle_missing_data(analysis_df, strategy='drop', threshold=0.5)
    
    logger.info(f"Analysis dataset created: {len(analysis_df)} records, {len(analysis_df.columns)} features")
    return analysis_df


def save_processed_data(df: pd.DataFrame, filename: str, output_dir: str = "data/processed"):
    """Save processed data to CSV"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / filename
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")
