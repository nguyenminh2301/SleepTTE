"""
Sleep-to-Brain Aging Signature Development
Builds multimodal models linking sleep features to brain aging biomarkers
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from src.data.utils import load_config
from src.visualization.plots import plot_feature_importance, plot_sleep_brain_heatmap
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_integrated_data():
    """Load sleep features and brain biomarkers"""
    logger.info("Loading integrated data...")
    
    # Load sleep features (from 02_sleep_features.py output)
    sleep_features = pd.read_csv('data/processed/sleep_features.csv')
    
    # Load brain biomarkers
    mri = pd.read_csv('data/processed/mri_processed.csv')
    clinical = pd.read_csv('data/processed/clinical_processed.csv')
    
    # Merge datasets
    data = sleep_features.merge(mri, on='participant_id', how='inner')
    data = data.merge(clinical, on='participant_id', how='inner')
    
    logger.info(f"Integrated data: {len(data)} participants, {len(data.columns)} features")
    return data


def select_sleep_features(data, config):
    """Select sleep feature columns"""
    feature_names = config['sleep_features']['features']
    
    # Get available features
    available_features = [f for f in feature_names if f in data.columns]
    
    logger.info(f"Selected {len(available_features)} sleep features")
    return available_features


def build_brain_aging_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_type: str = 'elastic_net'
) -> tuple:
    """
    Build predictive model for brain aging
    
    Args:
        X: Feature matrix (sleep features)
        y: Target variable (brain age delta or other biomarker)
        model_type: Type of model to use
    
    Returns:
        Tuple of (fitted model, predictions, metrics)
    """
    logger.info(f"Building {model_type} model...")
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Select model
    if model_type == 'elastic_net':
        model = ElasticNet(random_state=2026)
        param_grid = {
            'alpha': [0.001, 0.01, 0.1, 1.0],
            'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9]
        }
    elif model_type == 'ridge':
        model = Ridge(random_state=2026)
        param_grid = {'alpha': [0.001, 0.01, 0.1, 1.0, 10.0]}
    elif model_type == 'random_forest':
        model = RandomForestRegressor(n_estimators=100, random_state=2026)
        param_grid = {
            'max_depth': [3, 5, 10, None],
            'min_samples_split': [2, 5, 10]
        }
    elif model_type == 'gradient_boosting':
        model = GradientBoostingRegressor(n_estimators=100, random_state=2026)
        param_grid = {
            'learning_rate': [0.01, 0.1, 0.2],
            'max_depth': [3, 5, 7]
        }
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Grid search with cross-validation
    grid_search = GridSearchCV(
        model,
        param_grid,
        cv=5,
        scoring='neg_mean_absolute_error',
        n_jobs=-1
    )
    
    grid_search.fit(X_scaled, y)
    best_model = grid_search.best_estimator_
    
    # Cross-validated predictions
    cv_scores = cross_val_score(
        best_model,
        X_scaled,
        y,
        cv=5,
        scoring='neg_mean_absolute_error'
    )
    
    # Fit final model
    best_model.fit(X_scaled, y)
    predictions = best_model.predict(X_scaled)
    
    # Calculate metrics
    mae = mean_absolute_error(y, predictions)
    r2 = r2_score(y, predictions)
    
    metrics = {
        'mae': mae,
        'r2': r2,
        'cv_mae_mean': -cv_scores.mean(),
        'cv_mae_std': cv_scores.std(),
        'best_params': grid_search.best_params_
    }
    
    logger.info(f"Model performance: MAE={mae:.3f}, R²={r2:.3f}")
    logger.info(f"CV MAE: {-cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    
    return best_model, scaler, predictions, metrics


def calculate_sleep_brain_correlations(data, sleep_features, brain_biomarkers):
    """Calculate correlations between sleep features and brain biomarkers"""
    logger.info("Calculating sleep-brain correlations...")
    
    correlation_matrix = data[sleep_features + brain_biomarkers].corr().loc[
        sleep_features, brain_biomarkers
    ]
    
    return correlation_matrix


def generate_sleep_brain_signature(data, config):
    """Generate comprehensive sleep-to-brain aging signature"""
    logger.info("\n" + "=" * 80)
    logger.info("Generating Sleep-to-Brain Aging Signature")
    logger.info("=" * 80)
    
    # Select features
    sleep_features = select_sleep_features(data, config)
    brain_biomarkers = ['brain_age_delta', 'hippocampal_volume', 'entorhinal_thickness']
    
    # Prepare feature matrix
    X = data[sleep_features].fillna(data[sleep_features].median())
    
    results = {}
    
    # Build models for each brain biomarker
    for biomarker in brain_biomarkers:
        logger.info(f"\n[Biomarker: {biomarker}]")
        
        y = data[biomarker].fillna(data[biomarker].median())
        
        # Build model
        model, scaler, predictions, metrics = build_brain_aging_model(
            X, y, model_type='elastic_net'
        )
        
        results[biomarker] = {
            'model': model,
            'scaler': scaler,
            'predictions': predictions,
            'metrics': metrics
        }
        
        # Feature importance (for linear models)
        if hasattr(model, 'coef_'):
            feature_importance = pd.DataFrame({
                'feature': sleep_features,
                'coefficient': model.coef_,
                'abs_coefficient': np.abs(model.coef_)
            }).sort_values('abs_coefficient', ascending=False)
            
            logger.info(f"\nTop 5 features for {biomarker}:")
            for idx, row in feature_importance.head(5).iterrows():
                logger.info(f"  {row['feature']}: {row['coefficient']:.3f}")
            
            results[biomarker]['feature_importance'] = feature_importance
    
    # Calculate correlations
    correlation_matrix = calculate_sleep_brain_correlations(
        data, sleep_features, brain_biomarkers
    )
    results['correlations'] = correlation_matrix
    
    # Create visualizations
    logger.info("\nGenerating visualizations...")
    
    # Correlation heatmap
    fig = plot_sleep_brain_heatmap(correlation_matrix, 'outputs/figures/sleep_brain_correlations.png')
    plt.close(fig)
    
    # Feature importance plots
    for biomarker in brain_biomarkers:
        if 'feature_importance' in results[biomarker]:
            fi = results[biomarker]['feature_importance']
            plot_feature_importance(
                fi['feature'].values,
                fi['abs_coefficient'].values,
                f'outputs/figures/feature_importance_{biomarker}.png'
            )
    
    # Save results
    logger.info("\nSaving results...")
    
    # Save predictions
    predictions_df = data[['participant_id']].copy()
    for biomarker in brain_biomarkers:
        predictions_df[f'{biomarker}_actual'] = data[biomarker]
        predictions_df[f'{biomarker}_predicted'] = results[biomarker]['predictions']
    
    predictions_df.to_csv('outputs/tables/brain_aging_predictions.csv', index=False)
    
    # Save metrics
    metrics_df = pd.DataFrame([
        {
            'biomarker': biomarker,
            **results[biomarker]['metrics']
        }
        for biomarker in brain_biomarkers
    ])
    metrics_df.to_csv('outputs/tables/model_performance.csv', index=False)
    
    logger.info("\n" + "=" * 80)
    logger.info("Sleep-to-Brain Aging Signature Complete!")
    logger.info("=" * 80)
    
    return results


def main():
    """Main execution"""
    # Create output directories
    Path('outputs/figures').mkdir(parents=True, exist_ok=True)
    Path('outputs/tables').mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    config = load_config()
    
    # Load data
    data = load_integrated_data()
    
    # Generate signature
    results = generate_sleep_brain_signature(data, config)
    
    logger.info("\nNext steps:")
    logger.info("  1. Review model performance in outputs/tables/model_performance.csv")
    logger.info("  2. Examine correlations in outputs/figures/sleep_brain_correlations.png")
    logger.info("  3. Run 04_target_trial_design.py to emulate interventions")


if __name__ == "__main__":
    main()
