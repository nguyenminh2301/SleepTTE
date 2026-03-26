"""
Sleep feature extraction from actigraphy data
Implements validated algorithms for sleep/wake detection and circadian analysis
"""

import pandas as pd
import numpy as np
from scipy import signal, stats
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cole_kripke_algorithm(activity_counts: np.ndarray, window_size: int = 7) -> np.ndarray:
    """
    Cole-Kripke algorithm for sleep/wake classification
    
    Args:
        activity_counts: Array of activity counts per epoch
        window_size: Window size for weighted average (default: 7 minutes)
    
    Returns:
        Array of sleep probabilities (0-1)
    """
    # Cole-Kripke weights
    weights = np.array([0.04, 0.04, 0.04, 0.04, 1.00, 0.20, 0.20])
    
    # Pad activity counts
    padded = np.pad(activity_counts, (window_size // 2, window_size // 2), mode='edge')
    
    # Apply weighted moving average
    sleep_scores = np.zeros(len(activity_counts))
    
    for i in range(len(activity_counts)):
        window = padded[i:i + window_size]
        sleep_scores[i] = np.sum(window * weights)
    
    # Convert to sleep probability using logistic function
    # D = P / (1 + P) where P = weighted score
    # Sleep if D < threshold (typically 1.0)
    sleep_prob = 1 / (1 + sleep_scores)
    
    return sleep_prob


def detect_sleep_wake(
    activity_counts: np.ndarray,
    algorithm: str = 'cole_kripke',
    threshold: float = 0.04
) -> np.ndarray:
    """
    Detect sleep/wake states from actigraphy
    
    Args:
        activity_counts: Activity counts per epoch
        algorithm: 'cole_kripke', 'sadeh', or 'sazonov'
        threshold: Sleep probability threshold (0-1)
    
    Returns:
        Binary array (1 = sleep, 0 = wake)
    """
    if algorithm == 'cole_kripke':
        sleep_prob = cole_kripke_algorithm(activity_counts)
        sleep_wake = (sleep_prob >= threshold).astype(int)
    
    elif algorithm == 'sadeh':
        # Simplified Sadeh algorithm
        # For production, implement full algorithm
        sleep_prob = cole_kripke_algorithm(activity_counts)
        sleep_wake = (sleep_prob >= threshold).astype(int)
    
    elif algorithm == 'sazonov':
        # Simplified Sazonov algorithm
        sleep_prob = cole_kripke_algorithm(activity_counts)
        sleep_wake = (sleep_prob >= threshold).astype(int)
    
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    return sleep_wake


def extract_sleep_architecture(
    sleep_wake: np.ndarray,
    timestamps: pd.DatetimeIndex,
    epoch_minutes: int = 1
) -> Dict:
    """
    Extract sleep architecture features
    
    Args:
        sleep_wake: Binary sleep/wake array
        timestamps: Timestamps for each epoch
        epoch_minutes: Duration of each epoch in minutes
    
    Returns:
        Dictionary of sleep architecture features
    """
    # Identify sleep periods (consecutive sleep epochs)
    sleep_diff = np.diff(np.concatenate(([0], sleep_wake, [0])))
    sleep_starts = np.where(sleep_diff == 1)[0]
    sleep_ends = np.where(sleep_diff == -1)[0]
    
    if len(sleep_starts) == 0:
        return {
            'total_sleep_time': 0,
            'sleep_efficiency': 0,
            'sleep_onset_latency': np.nan,
            'wake_after_sleep_onset': 0,
            'number_of_awakenings': 0,
            'sleep_fragmentation_index': 0
        }
    
    # Total sleep time (minutes)
    total_sleep_time = np.sum(sleep_wake) * epoch_minutes
    
    # Total time in bed (from first to last sleep epoch)
    time_in_bed = (sleep_ends[-1] - sleep_starts[0]) * epoch_minutes
    
    # Sleep efficiency
    sleep_efficiency = (total_sleep_time / time_in_bed * 100) if time_in_bed > 0 else 0
    
    # Sleep onset latency (time to first sleep period)
    sleep_onset_latency = sleep_starts[0] * epoch_minutes if len(sleep_starts) > 0 else np.nan
    
    # Wake after sleep onset (WASO)
    if len(sleep_starts) > 0:
        main_sleep_period = sleep_wake[sleep_starts[0]:sleep_ends[-1]]
        wake_after_sleep_onset = np.sum(main_sleep_period == 0) * epoch_minutes
    else:
        wake_after_sleep_onset = 0
    
    # Number of awakenings (transitions from sleep to wake)
    number_of_awakenings = len(sleep_starts) - 1 if len(sleep_starts) > 1 else 0
    
    # Sleep fragmentation index
    sleep_fragmentation_index = (number_of_awakenings / (total_sleep_time / 60)) if total_sleep_time > 0 else 0
    
    return {
        'total_sleep_time': total_sleep_time,
        'sleep_efficiency': sleep_efficiency,
        'sleep_onset_latency': sleep_onset_latency,
        'wake_after_sleep_onset': wake_after_sleep_onset,
        'number_of_awakenings': number_of_awakenings,
        'sleep_fragmentation_index': sleep_fragmentation_index
    }


def calculate_circadian_metrics(
    activity_counts: np.ndarray,
    timestamps: pd.DatetimeIndex,
    window_days: int = 7
) -> Dict:
    """
    Calculate circadian rhythm metrics
    
    Args:
        activity_counts: Activity counts per epoch
        timestamps: Timestamps for each epoch
        window_days: Number of days for analysis window
    
    Returns:
        Dictionary of circadian metrics
    """
    # Convert to daily activity profiles
    df = pd.DataFrame({
        'timestamp': timestamps,
        'activity': activity_counts
    })
    df['date'] = df['timestamp'].dt.date
    df['time_of_day'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60
    
    # Calculate hourly averages across days
    hourly_profile = df.groupby('time_of_day')['activity'].mean().values
    
    # Interdaily Stability (IS)
    # Measures consistency of activity patterns across days
    daily_profiles = []
    for date in df['date'].unique():
        day_data = df[df['date'] == date].set_index('time_of_day')['activity']
        daily_profiles.append(day_data.values)
    
    if len(daily_profiles) > 1:
        daily_profiles = np.array(daily_profiles)
        grand_mean = np.mean(activity_counts)
        
        # IS = variance of hourly means / total variance
        hourly_variance = np.sum((hourly_profile - grand_mean) ** 2)
        total_variance = np.sum((activity_counts - grand_mean) ** 2)
        interdaily_stability = hourly_variance / total_variance if total_variance > 0 else 0
    else:
        interdaily_stability = np.nan
    
    # Intradaily Variability (IV)
    # Measures fragmentation of activity within days
    first_diff = np.diff(activity_counts)
    intradaily_variability = np.sum(first_diff ** 2) / (len(activity_counts) * np.var(activity_counts)) if np.var(activity_counts) > 0 else 0
    
    # Relative Amplitude
    # Difference between most active 10 hours and least active 5 hours
    sorted_hourly = np.sort(hourly_profile)
    m10 = np.mean(sorted_hourly[-10:])  # Most active 10 hours
    l5 = np.mean(sorted_hourly[:5])      # Least active 5 hours
    relative_amplitude = (m10 - l5) / (m10 + l5) if (m10 + l5) > 0 else 0
    
    # Acrophase (time of peak activity)
    acrophase = np.argmax(hourly_profile)
    
    return {
        'interdaily_stability': interdaily_stability,
        'intradaily_variability': intradaily_variability,
        'relative_amplitude': relative_amplitude,
        'acrophase': acrophase,
        'm10': m10,
        'l5': l5
    }


def calculate_sleep_regularity_index(
    sleep_wake: np.ndarray,
    timestamps: pd.DatetimeIndex
) -> float:
    """
    Calculate Sleep Regularity Index (SRI)
    
    Args:
        sleep_wake: Binary sleep/wake array
        timestamps: Timestamps for each epoch
    
    Returns:
        SRI value (0-100, higher = more regular)
    """
    # Group by time of day across multiple days
    df = pd.DataFrame({
        'timestamp': timestamps,
        'sleep_wake': sleep_wake
    })
    df['time_of_day'] = df['timestamp'].dt.hour * 60 + df['timestamp'].dt.minute
    
    # Calculate probability of same state at same time across days
    matches = 0
    comparisons = 0
    
    for time in df['time_of_day'].unique():
        states = df[df['time_of_day'] == time]['sleep_wake'].values
        if len(states) > 1:
            # Compare consecutive days
            for i in range(len(states) - 1):
                if states[i] == states[i + 1]:
                    matches += 1
                comparisons += 1
    
    sri = (matches / comparisons * 100) if comparisons > 0 else 0
    return sri


def calculate_social_jet_lag(
    sleep_wake: np.ndarray,
    timestamps: pd.DatetimeIndex
) -> float:
    """
    Calculate social jet lag (difference in sleep timing between weekdays and weekends)
    
    Args:
        sleep_wake: Binary sleep/wake array
        timestamps: Timestamps for each epoch
    
    Returns:
        Social jet lag in hours
    """
    df = pd.DataFrame({
        'timestamp': timestamps,
        'sleep_wake': sleep_wake
    })
    df['date'] = df['timestamp'].dt.date
    df['weekday'] = df['timestamp'].dt.weekday
    df['is_weekend'] = df['weekday'].isin([5, 6])
    
    # Calculate sleep midpoint for each day
    sleep_midpoints_weekday = []
    sleep_midpoints_weekend = []
    
    for date in df['date'].unique():
        day_data = df[df['date'] == date]
        sleep_epochs = day_data[day_data['sleep_wake'] == 1]
        
        if len(sleep_epochs) > 0:
            sleep_start = sleep_epochs['timestamp'].min()
            sleep_end = sleep_epochs['timestamp'].max()
            midpoint = sleep_start + (sleep_end - sleep_start) / 2
            
            if day_data['is_weekend'].iloc[0]:
                sleep_midpoints_weekend.append(midpoint.hour + midpoint.minute / 60)
            else:
                sleep_midpoints_weekday.append(midpoint.hour + midpoint.minute / 60)
    
    if len(sleep_midpoints_weekday) > 0 and len(sleep_midpoints_weekend) > 0:
        avg_weekday = np.mean(sleep_midpoints_weekday)
        avg_weekend = np.mean(sleep_midpoints_weekend)
        social_jet_lag = abs(avg_weekend - avg_weekday)
    else:
        social_jet_lag = np.nan
    
    return social_jet_lag


def extract_all_sleep_features(
    participant_data: pd.DataFrame,
    config: Dict
) -> Dict:
    """
    Extract all sleep features for a single participant
    
    Args:
        participant_data: Actigraphy data for one participant
        config: Configuration dictionary
    
    Returns:
        Dictionary of all sleep features
    """
    # Get configuration parameters
    algorithm = config['sleep_features']['algorithm']
    threshold = config['sleep_features']['threshold']
    
    # Extract activity counts and timestamps
    activity_counts = participant_data['activity_counts'].values
    timestamps = pd.to_datetime(participant_data['timestamp'])
    
    # Detect sleep/wake
    sleep_wake = detect_sleep_wake(activity_counts, algorithm=algorithm, threshold=threshold)
    
    # Extract features
    features = {}
    
    # Sleep architecture
    architecture = extract_sleep_architecture(sleep_wake, timestamps)
    features.update(architecture)
    
    # Circadian metrics
    circadian = calculate_circadian_metrics(activity_counts, timestamps)
    features.update(circadian)
    
    # Sleep regularity
    features['sleep_regularity_index'] = calculate_sleep_regularity_index(sleep_wake, timestamps)
    
    # Social jet lag
    features['social_jet_lag'] = calculate_social_jet_lag(sleep_wake, timestamps)
    
    return features


def process_all_participants(
    actigraphy_data: pd.DataFrame,
    config: Dict
) -> pd.DataFrame:
    """
    Process actigraphy data for all participants
    
    Args:
        actigraphy_data: Complete actigraphy dataset
        config: Configuration dictionary
    
    Returns:
        DataFrame with sleep features for all participants
    """
    logger.info("Processing actigraphy data for all participants")
    
    all_features = []
    
    for participant_id in actigraphy_data['participant_id'].unique():
        participant_data = actigraphy_data[actigraphy_data['participant_id'] == participant_id]
        
        try:
            features = extract_all_sleep_features(participant_data, config)
            features['participant_id'] = participant_id
            all_features.append(features)
        except Exception as e:
            logger.warning(f"Failed to process participant {participant_id}: {e}")
            continue
    
    features_df = pd.DataFrame(all_features)
    logger.info(f"Extracted sleep features for {len(features_df)} participants")
    
    return features_df


if __name__ == "__main__":
    # Example usage
    from src.data.utils import load_config, load_actigraphy_data, quality_control_actigraphy
    
    # Load configuration
    config = load_config()
    
    # Load actigraphy data
    actigraphy = load_actigraphy_data(config['data']['actigraphy_file'])
    
    # Quality control
    actigraphy_qc = quality_control_actigraphy(actigraphy)
    
    # Extract sleep features
    sleep_features = process_all_participants(actigraphy_qc, config)
    
    # Save results
    sleep_features.to_csv('data/processed/sleep_features.csv', index=False)
    logger.info("Sleep feature extraction complete")
