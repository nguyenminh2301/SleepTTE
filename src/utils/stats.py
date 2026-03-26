"""
Statistical utility functions for causal inference and effect estimation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict, StratifiedKFold
import statsmodels.api as sm
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def estimate_propensity_scores(
    X: pd.DataFrame,
    treatment: pd.Series,
    method: str = 'super_learner',
    base_learners: Optional[List[str]] = None,
    verbose: bool = True
) -> np.ndarray:
    """
    Estimate propensity scores for treatment assignment
    
    Args:
        X: Covariate matrix
        treatment: Binary treatment indicator
        method: 'logistic', 'gbm', 'random_forest', 'super_learner'
        base_learners: List of base learners for super learner
    
    Returns:
        Array of propensity scores (probability of treatment)
    """
    if verbose:
        logger.info(f"Estimating propensity scores using {method}")
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if method == 'logistic':
        model = LogisticRegression(max_iter=1000, random_state=2026)
        model.fit(X_scaled, treatment)
        ps = model.predict_proba(X_scaled)[:, 1]
    
    elif method == 'gbm':
        model = GradientBoostingClassifier(n_estimators=100, random_state=2026)
        model.fit(X_scaled, treatment)
        ps = model.predict_proba(X_scaled)[:, 1]
    
    elif method == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=2026)
        model.fit(X_scaled, treatment)
        ps = model.predict_proba(X_scaled)[:, 1]
    
    elif method == 'super_learner':
        # Ensemble of multiple models
        if base_learners is None:
            base_learners = ['logistic', 'gbm', 'random_forest']
        
        treatment_array = np.asarray(treatment).astype(int)
        class_counts = np.bincount(treatment_array)
        min_class_count = class_counts.min() if len(class_counts) > 1 else 0
        n_splits = min(5, min_class_count)

        if n_splits < 2:
            raise ValueError("Treatment must include at least 2 samples per class for super learner CV.")

        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=2026)
        predictions = []
        
        for learner in base_learners:
            if learner == 'logistic':
                model = LogisticRegression(max_iter=1000, random_state=2026)
            elif learner == 'gbm' or learner == 'gradient_boosting':
                model = GradientBoostingClassifier(n_estimators=100, random_state=2026)
            elif learner == 'random_forest':
                model = RandomForestClassifier(n_estimators=100, random_state=2026)
            elif learner == 'neural_network':
                model = MLPClassifier(
                    hidden_layer_sizes=(32, 16),
                    solver='lbfgs',
                    alpha=0.001,
                    max_iter=2000,
                    random_state=2026
                )
            else:
                continue
            
            # Cross-validated predictions
            pred = cross_val_predict(
                model,
                X_scaled,
                treatment,
                cv=cv,
                method='predict_proba',
                n_jobs=-1
            )[:, 1]
            predictions.append(pred)
        
        # Average predictions (simple ensemble)
        ps = np.mean(predictions, axis=0)
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Clip extreme values
    ps = np.clip(ps, 0.01, 0.99)
    
    if verbose:
        logger.info(f"Propensity scores estimated. Mean: {ps.mean():.3f}, Range: [{ps.min():.3f}, {ps.max():.3f}]")
    return ps


def calculate_iptw_weights(
    treatment: pd.Series,
    propensity_scores: np.ndarray,
    stabilized: bool = True,
    truncate_percentiles: Optional[Tuple[float, float]] = (1, 99),
    verbose: bool = True
) -> np.ndarray:
    """
    Calculate inverse probability of treatment weights (IPTW)
    
    Args:
        treatment: Binary treatment indicator
        propensity_scores: Estimated propensity scores
        stabilized: Whether to use stabilized weights
        truncate_percentiles: Percentiles for weight truncation
    
    Returns:
        Array of IPTW weights
    """
    if verbose:
        logger.info("Calculating IPTW weights")
    
    # Calculate weights
    weights = np.where(
        treatment == 1,
        1 / propensity_scores,
        1 / (1 - propensity_scores)
    )
    
    # Stabilized weights
    if stabilized:
        p_treatment = treatment.mean()
        weights = np.where(
            treatment == 1,
            p_treatment / propensity_scores,
            (1 - p_treatment) / (1 - propensity_scores)
        )
    
    # Truncate extreme weights
    if truncate_percentiles is not None:
        lower, upper = truncate_percentiles
        lower_bound = np.percentile(weights, lower)
        upper_bound = np.percentile(weights, upper)
        weights = np.clip(weights, lower_bound, upper_bound)
        if verbose:
            logger.info(f"Weights truncated at {lower}th and {upper}th percentiles")
    
    if verbose:
        logger.info(f"IPTW weights calculated. Mean: {weights.mean():.3f}, Range: [{weights.min():.3f}, {weights.max():.3f}]")
    return weights


def assess_covariate_balance(
    X: pd.DataFrame,
    treatment: pd.Series,
    weights: Optional[np.ndarray] = None
) -> pd.DataFrame:
    """
    Assess covariate balance using standardized mean differences (SMD)
    
    Args:
        X: Covariate matrix
        treatment: Binary treatment indicator
        weights: Optional IPTW weights
    
    Returns:
        DataFrame with SMD for each covariate
    """
    logger.info("Assessing covariate balance")
    
    balance_results = []
    
    for col in X.columns:
        # Unweighted SMD
        mean_treated = X.loc[treatment == 1, col].mean()
        mean_control = X.loc[treatment == 0, col].mean()
        
        var_treated = X.loc[treatment == 1, col].var()
        var_control = X.loc[treatment == 0, col].var()
        pooled_sd = np.sqrt((var_treated + var_control) / 2)
        
        smd_unweighted = (mean_treated - mean_control) / pooled_sd if pooled_sd > 0 else 0
        
        # Weighted SMD
        if weights is not None:
            weights_treated = weights[treatment == 1]
            weights_control = weights[treatment == 0]
            
            mean_treated_w = np.average(X.loc[treatment == 1, col], weights=weights_treated)
            mean_control_w = np.average(X.loc[treatment == 0, col], weights=weights_control)
            
            var_treated_w = np.average((X.loc[treatment == 1, col] - mean_treated_w)**2, weights=weights_treated)
            var_control_w = np.average((X.loc[treatment == 0, col] - mean_control_w)**2, weights=weights_control)
            pooled_sd_w = np.sqrt((var_treated_w + var_control_w) / 2)
            
            smd_weighted = (mean_treated_w - mean_control_w) / pooled_sd_w if pooled_sd_w > 0 else 0
        else:
            smd_weighted = np.nan
        
        balance_results.append({
            'covariate': col,
            'smd_unweighted': smd_unweighted,
            'smd_weighted': smd_weighted
        })
    
    balance_df = pd.DataFrame(balance_results)
    
    # Flag imbalanced covariates
    balance_df['balanced'] = np.abs(balance_df['smd_weighted']) < 0.1
    
    n_imbalanced = (~balance_df['balanced']).sum()
    logger.info(f"Covariate balance assessed. {n_imbalanced}/{len(balance_df)} covariates remain imbalanced (|SMD| >= 0.1)")
    
    return balance_df


def estimate_ate(
    outcome: pd.Series,
    treatment: pd.Series,
    weights: np.ndarray,
    outcome_type: str = 'continuous',
    verbose: bool = True
) -> Dict:
    """
    Estimate average treatment effect (ATE) using IPTW
    
    Args:
        outcome: Outcome variable
        treatment: Binary treatment indicator
        weights: IPTW weights
        outcome_type: 'continuous' or 'binary'
    
    Returns:
        Dictionary with ATE estimate and standard error
    """
    if verbose:
        logger.info(f"Estimating ATE for {outcome_type} outcome")
    
    if outcome_type == 'continuous':
        # Weighted mean difference
        mean_treated = np.average(outcome[treatment == 1], weights=weights[treatment == 1])
        mean_control = np.average(outcome[treatment == 0], weights=weights[treatment == 0])
        
        ate = mean_treated - mean_control
        
        # Standard error using robust sandwich estimator
        # Simplified version - for production, use more sophisticated methods
        var_treated = np.average((outcome[treatment == 1] - mean_treated)**2, weights=weights[treatment == 1])
        var_control = np.average((outcome[treatment == 0] - mean_control)**2, weights=weights[treatment == 0])
        
        n_treated = (treatment == 1).sum()
        n_control = (treatment == 0).sum()
        
        se = np.sqrt(var_treated / n_treated + var_control / n_control)
        
    elif outcome_type == 'binary':
        # Risk difference
        risk_treated = np.average(outcome[treatment == 1], weights=weights[treatment == 1])
        risk_control = np.average(outcome[treatment == 0], weights=weights[treatment == 0])
        
        ate = risk_treated - risk_control
        
        # Standard error
        var_treated = risk_treated * (1 - risk_treated)
        var_control = risk_control * (1 - risk_control)
        
        n_treated = (treatment == 1).sum()
        n_control = (treatment == 0).sum()
        
        se = np.sqrt(var_treated / n_treated + var_control / n_control)
    
    else:
        raise ValueError(f"Unknown outcome type: {outcome_type}")
    
    # 95% CI
    ci_lower = ate - 1.96 * se
    ci_upper = ate + 1.96 * se
    
    # P-value
    z_stat = ate / se
    p_value = 2 * (1 - stats.norm.cdf(np.abs(z_stat)))
    
    results = {
        'ate': ate,
        'se': se,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'z_stat': z_stat,
        'p_value': p_value
    }
    
    if verbose:
        logger.info(f"ATE: {ate:.3f} (95% CI: [{ci_lower:.3f}, {ci_upper:.3f}], p={p_value:.4f})")
    return results


def bootstrap_ci(
    data: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    covariate_cols: List[str],
    n_iterations: int = 1000,
    ci_level: float = 0.95,
    random_seed: int = 2026
) -> Dict:
    """
    Calculate bootstrap confidence intervals for ATE
    
    Args:
        data: Complete dataset
        outcome_col: Name of outcome column
        treatment_col: Name of treatment column
        covariate_cols: List of covariate column names
        n_iterations: Number of bootstrap iterations
        ci_level: Confidence level
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with bootstrap results
    """
    logger.info(f"Running bootstrap with {n_iterations} iterations")
    
    np.random.seed(random_seed)
    ate_estimates = []
    
    n = len(data)
    
    for i in range(n_iterations):
        # Resample with replacement
        boot_indices = np.random.choice(n, size=n, replace=True)
        boot_data = data.iloc[boot_indices].copy()
        
        # Estimate propensity scores
        X_boot = boot_data[covariate_cols]
        treatment_boot = boot_data[treatment_col]
        outcome_boot = boot_data[outcome_col]
        
        try:
            ps_boot = estimate_propensity_scores(
                X_boot,
                treatment_boot,
                method='logistic',
                verbose=False
            )
            weights_boot = calculate_iptw_weights(
                treatment_boot,
                ps_boot,
                stabilized=True,
                verbose=False
            )
            
            # Estimate ATE
            ate_boot = estimate_ate(
                outcome_boot,
                treatment_boot,
                weights_boot,
                outcome_type='continuous',
                verbose=False
            )
            ate_estimates.append(ate_boot['ate'])
        except:
            # Skip failed iterations
            continue
        
        if (i + 1) % 100 == 0:
            logger.info(f"Bootstrap iteration {i + 1}/{n_iterations}")
    
    ate_estimates = np.array(ate_estimates)
    
    # Calculate percentile CI
    alpha = 1 - ci_level
    ci_lower = np.percentile(ate_estimates, alpha / 2 * 100)
    ci_upper = np.percentile(ate_estimates, (1 - alpha / 2) * 100)
    
    results = {
        'ate_mean': ate_estimates.mean(),
        'ate_median': np.median(ate_estimates),
        'ate_sd': ate_estimates.std(),
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'n_iterations': len(ate_estimates)
    }
    
    logger.info(f"Bootstrap complete. ATE: {results['ate_mean']:.3f} (95% CI: [{ci_lower:.3f}, {ci_upper:.3f}])")
    return results


def calculate_e_value(ate: float, ci_lower: float) -> Dict:
    """
    Calculate E-value for sensitivity to unmeasured confounding
    
    Args:
        ate: Average treatment effect (risk ratio or hazard ratio scale)
        ci_lower: Lower bound of confidence interval
    
    Returns:
        Dictionary with E-values
    """
    # Convert to risk ratio scale if needed
    # E-value formula: RR + sqrt(RR * (RR - 1))
    
    if ate <= 0:
        logger.warning("E-value calculation requires positive effect estimate")
        return {'e_value_point': np.nan, 'e_value_ci': np.nan}
    
    # Point estimate E-value
    e_value_point = ate + np.sqrt(ate * (ate - 1))
    
    # CI E-value
    if ci_lower > 1:
        e_value_ci = ci_lower + np.sqrt(ci_lower * (ci_lower - 1))
    else:
        e_value_ci = 1.0
    
    results = {
        'e_value_point': e_value_point,
        'e_value_ci': e_value_ci
    }
    
    logger.info(f"E-value (point): {e_value_point:.2f}, E-value (CI): {e_value_ci:.2f}")
    return results


def fit_outcome_model(
    data: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    covariate_cols: List[str],
    weights: Optional[np.ndarray] = None,
    model_type: str = 'linear'
) -> sm.regression.linear_model.RegressionResultsWrapper:
    """
    Fit weighted outcome regression model
    
    Args:
        data: Dataset
        outcome_col: Outcome variable name
        treatment_col: Treatment variable name
        covariate_cols: List of covariate names
        weights: Optional IPTW weights
        model_type: 'linear' or 'logistic'
    
    Returns:
        Fitted statsmodels regression results
    """
    # Prepare data
    y = data[outcome_col]
    X = data[[treatment_col] + covariate_cols]
    X = sm.add_constant(X)
    
    # Fit model
    if model_type == 'linear':
        if weights is not None:
            model = sm.WLS(y, X, weights=weights)
        else:
            model = sm.OLS(y, X)
    elif model_type == 'logistic':
        if weights is not None:
            model = sm.Logit(y, X)
            # Note: statsmodels Logit doesn't directly support weights in the same way
            # For production, use GEE or other weighted methods
        else:
            model = sm.Logit(y, X)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    results = model.fit()
    return results
