"""
Target Trial Emulation Framework
Emulates randomized trials for sleep interventions using observational data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.data.utils import load_config
from src.utils.stats import (
    estimate_propensity_scores,
    calculate_iptw_weights,
    assess_covariate_balance,
    estimate_ate,
    bootstrap_ci
)
from src.visualization.plots import plot_love_plot, plot_forest_plot
from lifelines import CoxPHFitter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def define_trial_eligibility(data, trial_name, config):
    """
    Define eligibility criteria for each target trial
    
    Args:
        data: Complete dataset
        trial_name: 'dcbt_i', 'osa_treatment', or 'circadian_regularity'
        config: Configuration dictionary
    
    Returns:
        DataFrame with eligible participants
    """
    logger.info(f"Defining eligibility for {trial_name} trial...")
    
    trial_config = config['target_trials'][trial_name]
    eligible = data.copy()
    
    # Apply eligibility criteria based on trial type
    if trial_name == 'dcbt_i':
        # Insomnia criteria: low sleep efficiency
        eligible = eligible[eligible['sleep_efficiency'] < 85]
        logger.info(f"  - Sleep efficiency < 85%: {len(eligible)} participants")
    
    elif trial_name == 'osa_treatment':
        # OSA criteria: high fragmentation (proxy for AHI)
        # In real data, use actual AHI from polysomnography
        eligible = eligible[eligible['sleep_fragmentation_index'] > 15]
        logger.info(f"  - High sleep fragmentation: {len(eligible)} participants")
    
    elif trial_name == 'circadian_regularity':
        # Circadian irregularity criteria
        eligible = eligible[
            (eligible['sleep_regularity_index'] < 70) |
            (eligible['social_jet_lag'] > 2)
        ]
        logger.info(f"  - Circadian irregularity: {len(eligible)} participants")
    
    else:
        raise ValueError(f"Unknown trial: {trial_name}")
    
    logger.info(f"Eligible participants: {len(eligible)}/{len(data)}")
    return eligible


def define_treatment_exposure(data, trial_name, config):
    """
    Define treatment exposure for each trial
    
    Args:
        data: Eligible participants
        trial_name: Trial identifier
        config: Configuration dictionary
    
    Returns:
        DataFrame with treatment indicator
    """
    logger.info(f"Defining treatment exposure for {trial_name}...")
    
    # In real data, this would be based on actual intervention receipt
    # For demonstration, simulate treatment based on baseline characteristics
    
    np.random.seed(2026)
    
    if trial_name == 'dcbt_i':
        # Treatment: Completed dCBT-I program
        # Simulate based on education and age (proxy for adherence)
        prob_treatment = 0.3 + 0.1 * (data['education_years'] - data['education_years'].mean()) / data['education_years'].std()
        prob_treatment = prob_treatment.clip(0.1, 0.7)
        data['treatment'] = np.random.binomial(1, prob_treatment)
    
    elif trial_name == 'osa_treatment':
        # Treatment: CPAP adherence
        prob_treatment = 0.4 + 0.05 * (data['age'] - data['age'].mean()) / data['age'].std()
        prob_treatment = prob_treatment.clip(0.2, 0.6)
        data['treatment'] = np.random.binomial(1, prob_treatment)
    
    elif trial_name == 'circadian_regularity':
        # Treatment: Achieved circadian regularity
        prob_treatment = 0.35
        data['treatment'] = np.random.binomial(1, prob_treatment, len(data))
    
    logger.info(f"Treatment group: {data['treatment'].sum()}/{len(data)} ({data['treatment'].mean()*100:.1f}%)")
    return data


def select_confounders(data):
    """Select confounding variables for adjustment"""
    confounders = [
        'age', 'education_years', 'bmi',
        'apoe4_status', 'hypertension', 'diabetes'
    ]
    
    # Create dummy variables for categorical variables
    data_with_dummies = pd.get_dummies(data, columns=['sex', 'cognitive_status'], drop_first=True)
    
    # Add sex and cognitive status dummies to confounders
    sex_cols = [col for col in data_with_dummies.columns if col.startswith('sex_')]
    cog_cols = [col for col in data_with_dummies.columns if col.startswith('cognitive_status_')]
    
    all_confounders = confounders + sex_cols + cog_cols
    available_confounders = [c for c in all_confounders if c in data_with_dummies.columns]
    
    return data_with_dummies, available_confounders


def emulate_single_trial(data, trial_name, config):
    """
    Emulate a single target trial
    
    Args:
        data: Complete dataset
        trial_name: Trial identifier
        config: Configuration dictionary
    
    Returns:
        Dictionary with trial results
    """
    logger.info("\n" + "=" * 80)
    logger.info(f"Emulating Target Trial: {trial_name.upper()}")
    logger.info("=" * 80)
    
    # Step 1: Define eligibility
    eligible_data = define_trial_eligibility(data, trial_name, config)
    
    # Step 2: Define treatment
    trial_data = define_treatment_exposure(eligible_data, trial_name, config)
    
    # Step 3: Select confounders
    trial_data, confounders = select_confounders(trial_data)
    
    # Step 4: Estimate propensity scores
    logger.info("\n[Propensity Score Estimation]")
    X = trial_data[confounders].fillna(trial_data[confounders].median())
    treatment = trial_data['treatment']
    
    ps = estimate_propensity_scores(
        X, treatment,
        method=config['causal_inference']['ps_method'],
        base_learners=config['causal_inference']['base_learners']
    )
    
    # Step 5: Calculate IPTW weights
    logger.info("\n[IPTW Weight Calculation]")
    weights = calculate_iptw_weights(
        treatment, ps,
        stabilized=config['causal_inference']['stabilized_weights'],
        truncate_percentiles=(
            config['causal_inference']['weight_truncation']['lower_percentile'],
            config['causal_inference']['weight_truncation']['upper_percentile']
        )
    )
    
    # Step 6: Assess covariate balance
    logger.info("\n[Covariate Balance Assessment]")
    balance_df = assess_covariate_balance(X, treatment, weights)
    
    # Create Love plot
    love_fig = plot_love_plot(
        balance_df,
        f'outputs/figures/love_plot_{trial_name}.png',
        threshold=config['causal_inference']['smd_threshold']
    )
    
    # Step 7: Estimate treatment effects
    logger.info("\n[Treatment Effect Estimation]")
    
    results = {}
    
    # Outcome 1: Brain age delta
    if 'brain_age_delta' in trial_data.columns:
        ate_brain_age = estimate_ate(
            trial_data['brain_age_delta'],
            treatment,
            weights,
            outcome_type='continuous'
        )
        results['brain_age_delta'] = ate_brain_age
        logger.info(f"Brain Age Delta ATE: {ate_brain_age['ate']:.3f} (95% CI: [{ate_brain_age['ci_lower']:.3f}, {ate_brain_age['ci_upper']:.3f}])")
    
    # Outcome 2: Hippocampal volume
    if 'hippocampal_volume' in trial_data.columns:
        ate_hippo = estimate_ate(
            trial_data['hippocampal_volume'],
            treatment,
            weights,
            outcome_type='continuous'
        )
        results['hippocampal_volume'] = ate_hippo
        logger.info(f"Hippocampal Volume ATE: {ate_hippo['ate']:.3f} (95% CI: [{ate_hippo['ci_lower']:.3f}, {ate_hippo['ci_upper']:.3f}])")
    
    # Step 8: Bootstrap confidence intervals
    logger.info("\n[Bootstrap Confidence Intervals]")
    
    # Prepare data for bootstrap
    boot_data = trial_data[confounders + ['treatment', 'brain_age_delta']].copy()
    
    boot_results = bootstrap_ci(
        boot_data,
        outcome_col='brain_age_delta',
        treatment_col='treatment',
        covariate_cols=confounders,
        n_iterations=config['causal_inference']['bootstrap_iterations'],
        ci_level=config['causal_inference']['bootstrap_ci_level']
    )
    
    results['bootstrap'] = boot_results
    
    # Save results
    results['trial_name'] = trial_name
    results['n_eligible'] = len(eligible_data)
    results['n_treated'] = treatment.sum()
    results['n_control'] = len(treatment) - treatment.sum()
    results['balance'] = balance_df
    results['weights'] = weights
    
    return results


def run_all_trials(data, config):
    """Run all three target trial emulations"""
    logger.info("\n" + "=" * 80)
    logger.info("TARGET TRIAL EMULATION: ALL INTERVENTIONS")
    logger.info("=" * 80)
    
    trials = ['dcbt_i', 'osa_treatment', 'circadian_regularity']
    all_results = {}
    
    for trial in trials:
        results = emulate_single_trial(data, trial, config)
        all_results[trial] = results
    
    # Comparative effectiveness
    logger.info("\n" + "=" * 80)
    logger.info("COMPARATIVE EFFECTIVENESS")
    logger.info("=" * 80)
    
    comparison_data = []
    for trial, results in all_results.items():
        if 'brain_age_delta' in results:
            comparison_data.append({
                'intervention': trial.replace('_', ' ').title(),
                'ate': results['brain_age_delta']['ate'],
                'ci_lower': results['brain_age_delta']['ci_lower'],
                'ci_upper': results['brain_age_delta']['ci_upper'],
                'p_value': results['brain_age_delta']['p_value']
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create forest plot
    forest_fig = plot_forest_plot(
        comparison_df,
        output_path='outputs/figures/comparative_effectiveness_forest.png'
    )
    
    # Save comparison table
    comparison_df.to_csv('outputs/tables/comparative_effectiveness.csv', index=False)
    
    logger.info("\nComparative Effectiveness Results:")
    print(comparison_df.to_string(index=False))
    
    return all_results, comparison_df


def main():
    """Main execution"""
    # Create output directories
    Path('outputs/figures').mkdir(parents=True, exist_ok=True)
    Path('outputs/tables').mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    config = load_config()
    
    # Load integrated data
    logger.info("Loading integrated data...")
    sleep_features = pd.read_csv('data/processed/sleep_features.csv')
    mri = pd.read_csv('data/processed/mri_processed.csv')
    clinical = pd.read_csv('data/processed/clinical_processed.csv')
    
    # Merge
    data = sleep_features.merge(mri, on='participant_id', how='inner')
    data = data.merge(clinical, on='participant_id', how='inner')
    
    # Run all trials
    all_results, comparison_df = run_all_trials(data, config)
    
    logger.info("\n" + "=" * 80)
    logger.info("TARGET TRIAL EMULATION COMPLETE!")
    logger.info("=" * 80)
    logger.info("\nResults saved to:")
    logger.info("  - outputs/tables/comparative_effectiveness.csv")
    logger.info("  - outputs/figures/comparative_effectiveness_forest.png")
    logger.info("  - outputs/figures/love_plot_*.png")


if __name__ == "__main__":
    main()
