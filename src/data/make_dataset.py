"""
Data processing and integration pipeline
Loads and harmonizes multimodal data from PREVENT-AD
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.data.utils import (
    load_config,
    load_actigraphy_data,
    load_biomarker_data,
    load_clinical_data,
    quality_control_actigraphy,
    merge_multimodal_data,
    handle_missing_data,
    save_processed_data
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main data processing pipeline"""
    logger.info("=" * 80)
    logger.info("TTE2026_sleep: Data Processing Pipeline")
    logger.info("=" * 80)
    
    # Load configuration
    config = load_config()
    
    # Create output directories
    Path(config['data']['processed_dir']).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load raw data
    logger.info("\n[Step 1] Loading raw data...")
    
    try:
        clinical = load_clinical_data(config['data']['clinical_file'])
        logger.info(f"✓ Loaded clinical data: {len(clinical)} participants")
    except FileNotFoundError:
        logger.warning("Clinical data file not found. Creating sample data...")
        clinical = create_sample_clinical_data()
        save_processed_data(clinical, 'clinical_data.csv', 'data/raw')
    
    try:
        actigraphy = load_actigraphy_data(config['data']['actigraphy_file'])
        logger.info(f"✓ Loaded actigraphy data: {len(actigraphy)} records")
    except FileNotFoundError:
        logger.warning("Actigraphy data file not found. Creating sample data...")
        actigraphy = create_sample_actigraphy_data()
        save_processed_data(actigraphy, 'actigraphy.csv', 'data/raw')
    
    try:
        mri = load_biomarker_data(config['data']['mri_file'], 'MRI')
        logger.info(f"✓ Loaded MRI data: {len(mri)} participants")
    except FileNotFoundError:
        logger.warning("MRI data file not found. Creating sample data...")
        mri = create_sample_mri_data(clinical)
        save_processed_data(mri, 'mri_biomarkers.csv', 'data/raw')
    
    # Optional biomarkers
    try:
        pet = load_biomarker_data(config['data']['pet_file'], 'PET')
        logger.info(f"✓ Loaded PET data: {len(pet)} participants")
    except FileNotFoundError:
        logger.info("PET data not available, proceeding without it")
        pet = None
    
    try:
        plasma = load_biomarker_data(config['data']['plasma_file'], 'Plasma')
        logger.info(f"✓ Loaded plasma data: {len(plasma)} participants")
    except FileNotFoundError:
        logger.info("Plasma data not available, proceeding without it")
        plasma = None
    
    # Step 2: Quality control
    logger.info("\n[Step 2] Applying quality control...")
    actigraphy_qc = quality_control_actigraphy(
        actigraphy,
        min_wear_time_hours=20,
        min_valid_days=5
    )
    
    # Step 3: Merge multimodal data
    logger.info("\n[Step 3] Merging multimodal data...")
    # Note: Actigraphy will be aggregated to participant level in 02_sleep_features.py
    
    # Step 4: Save processed data
    logger.info("\n[Step 4] Saving processed data...")
    save_processed_data(clinical, 'clinical_processed.csv')
    save_processed_data(actigraphy_qc, 'actigraphy_qc.csv')
    save_processed_data(mri, 'mri_processed.csv')
    
    if pet is not None:
        save_processed_data(pet, 'pet_processed.csv')
    if plasma is not None:
        save_processed_data(plasma, 'plasma_processed.csv')
    
    logger.info("\n" + "=" * 80)
    logger.info("Data processing complete!")
    logger.info("=" * 80)
    logger.info(f"\nProcessed data saved to: {config['data']['processed_dir']}")
    logger.info("\nNext steps:")
    logger.info("  1. Run 02_sleep_features.py to extract sleep features")
    logger.info("  2. Run 03_brain_aging_signature.py to build predictive models")
    logger.info("  3. Run 04_target_trial_design.py to emulate interventions")


def create_sample_clinical_data(n=200):
    """Create sample clinical data for demonstration"""
    np.random.seed(2026)
    
    data = {
        'participant_id': [f'P{i:04d}' for i in range(1, n+1)],
        'age': np.random.normal(70, 8, n).clip(55, 90),
        'sex': np.random.choice(['M', 'F'], n),
        'education_years': np.random.normal(14, 3, n).clip(8, 20),
        'apoe4_status': np.random.choice([0, 1, 2], n, p=[0.6, 0.3, 0.1]),
        'cognitive_status': np.random.choice(['CU', 'MCI'], n, p=[0.85, 0.15]),
        'bmi': np.random.normal(26, 4, n).clip(18, 40),
        'hypertension': np.random.choice([0, 1], n, p=[0.6, 0.4]),
        'diabetes': np.random.choice([0, 1], n, p=[0.85, 0.15])
    }
    
    return pd.DataFrame(data)


def create_sample_actigraphy_data(n_participants=50, days=7):
    """Create sample actigraphy data"""
    np.random.seed(2026)
    
    data = []
    for i in range(1, n_participants+1):
        participant_id = f'P{i:04d}'
        
        # Generate 7 days of minute-by-minute data
        timestamps = pd.date_range('2024-01-01', periods=days*24*60, freq='1min')
        
        # Simulate activity pattern (higher during day, lower at night)
        hour_of_day = timestamps.hour.values + timestamps.minute.values / 60
        base_activity = 100 * (1 + np.sin((hour_of_day - 6) * np.pi / 12))
        noise = np.random.exponential(50, len(timestamps))
        activity_counts = np.clip(base_activity + noise, 0, 500)
        
        # Add sleep periods (lower activity 11pm-7am)
        night_mask = (timestamps.hour >= 23) | (timestamps.hour < 7)
        activity_counts[night_mask] *= 0.1
        
        for j, (ts, act) in enumerate(zip(timestamps, activity_counts)):
            data.append({
                'participant_id': participant_id,
                'timestamp': ts,
                'activity_counts': act,
                'wear_time': 1
            })
    
    return pd.DataFrame(data)


def create_sample_mri_data(clinical_df):
    """Create sample MRI biomarker data"""
    np.random.seed(2026)
    
    n = len(clinical_df)
    
    # Brain age delta correlated with chronological age
    brain_age_delta = np.random.normal(0, 5, n) + (clinical_df['age'].values - 70) * 0.2
    
    data = {
        'participant_id': clinical_df['participant_id'],
        'visit_date': pd.date_range('2024-01-01', periods=n, freq='1D'),
        'brain_age': clinical_df['age'].values + brain_age_delta,
        'brain_age_delta': brain_age_delta,
        'hippocampal_volume': np.random.normal(7000, 800, n),
        'entorhinal_thickness': np.random.normal(3.5, 0.4, n),
        'total_gray_matter': np.random.normal(600, 50, n),
        'white_matter_hyperintensities': np.random.exponential(2, n)
    }
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    main()
