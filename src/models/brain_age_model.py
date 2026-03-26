"""
Sleep-to-Brain Aging Signature Development
Builds multimodal models linking sleep features to brain aging biomarkers
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings
sys.path.append(str(Path(__file__).parent.parent))

from sklearn.model_selection import cross_val_score, cross_val_predict, GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.exceptions import ConvergenceWarning
import matplotlib.pyplot as plt
import seaborn as sns
from src.data.utils import load_config
from src.visualization.plots import plot_feature_importance, plot_sleep_brain_heatmap
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_feature_matrix(X: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare model feature matrix and ensure no NaN values remain.
    """
    X_prepared = X.copy()

    # Median imputation first, then handle all-NaN columns with zeros.
    medians = X_prepared.median(numeric_only=True)
    X_prepared = X_prepared.fillna(medians)

    remaining_nan_cols = X_prepared.columns[X_prepared.isna().any()].tolist()
    if remaining_nan_cols:
        logger.warning(
            "Columns with all-missing values detected; filling with 0: %s",
            remaining_nan_cols
        )
        X_prepared[remaining_nan_cols] = X_prepared[remaining_nan_cols].fillna(0.0)

    return X_prepared


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
    model_type: str = 'auto'
) -> tuple:
    """
    Build predictive model for brain aging
    
    Args:
        X: Feature matrix (sleep features)
        y: Target variable (brain age delta or other biomarker)
        model_type: Type of model to use. Use 'auto' to select the best model by OOF MAE.
    
    Returns:
        Tuple of (fitted model, predictions, metrics)
    """
    logger.info(f"Building model: {model_type}")

    X_prepared = prepare_feature_matrix(X)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_prepared)
    cv_strategy = KFold(n_splits=5, shuffle=True, random_state=2026)

    model_candidates = {
        'dummy_mean': (
            DummyRegressor(strategy='mean'),
            None
        ),
        'ridge': (
            Ridge(random_state=2026),
            {'alpha': [0.01, 0.1, 1.0, 10.0, 100.0]}
        ),
        'elastic_net': (
            ElasticNet(random_state=2026, max_iter=20000, tol=1e-3),
            {'alpha': [0.01, 0.1, 1.0, 10.0], 'l1_ratio': [0.2, 0.5, 0.8]}
        ),
        'random_forest': (
            RandomForestRegressor(n_estimators=200, random_state=2026),
            {'max_depth': [3, 5, 10, None], 'min_samples_split': [2, 5, 10]}
        ),
        'gradient_boosting': (
            GradientBoostingRegressor(n_estimators=200, random_state=2026),
            {'learning_rate': [0.01, 0.05, 0.1], 'max_depth': [2, 3, 5]}
        ),
    }

    if model_type != 'auto':
        if model_type not in model_candidates:
            raise ValueError(f"Unknown model type: {model_type}")
        model_candidates = {model_type: model_candidates[model_type]}

    leaderboard_rows = []
    best_name = None
    best_estimator = None
    best_predictions = None
    best_scores = None
    best_params = {}
    best_cv_mae = np.inf

    for candidate_name, (candidate_model, candidate_grid) in model_candidates.items():
        logger.info("Evaluating candidate: %s", candidate_name)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            if candidate_grid:
                search = GridSearchCV(
                    candidate_model,
                    candidate_grid,
                    cv=cv_strategy,
                    scoring='neg_mean_absolute_error',
                    n_jobs=-1,
                    error_score='raise'
                )
                search.fit(X_scaled, y)
                estimator = search.best_estimator_
                params = search.best_params_
            else:
                estimator = candidate_model
                estimator.fit(X_scaled, y)
                params = {}

            cv_predictions = cross_val_predict(
                estimator,
                X_scaled,
                y,
                cv=cv_strategy,
                n_jobs=-1
            )
            cv_scores = cross_val_score(
                estimator,
                X_scaled,
                y,
                cv=cv_strategy,
                scoring='neg_mean_absolute_error',
                n_jobs=-1
            )

        cv_mae = mean_absolute_error(y, cv_predictions)
        cv_r2 = r2_score(y, cv_predictions)
        leaderboard_rows.append(
            {
                'model': candidate_name,
                'cv_mae': cv_mae,
                'cv_r2': cv_r2,
                'cv_mae_std': cv_scores.std(),
                'best_params': params,
            }
        )

        if cv_mae < best_cv_mae:
            best_cv_mae = cv_mae
            best_name = candidate_name
            best_estimator = estimator
            best_predictions = cv_predictions
            best_scores = cv_scores
            best_params = params

    best_estimator.fit(X_scaled, y)
    train_predictions = best_estimator.predict(X_scaled)

    train_mae = mean_absolute_error(y, train_predictions)
    train_r2 = r2_score(y, train_predictions)
    cv_mae = mean_absolute_error(y, best_predictions)
    cv_r2 = r2_score(y, best_predictions)

    metrics = {
        'selected_model': best_name,
        'train_mae': train_mae,
        'train_r2': train_r2,
        'cv_mae': cv_mae,
        'cv_r2': cv_r2,
        'cv_mae_mean': -best_scores.mean(),
        'cv_mae_std': best_scores.std(),
        'best_params': best_params,
    }

    logger.info("Selected model: %s", best_name)
    logger.info(f"Train performance: MAE={train_mae:.3f}, R2={train_r2:.3f}")
    logger.info(f"OOF performance: MAE={cv_mae:.3f}, R2={cv_r2:.3f}")
    logger.info(f"CV MAE: {-best_scores.mean():.3f} ± {best_scores.std():.3f}")

    leaderboard_df = pd.DataFrame(leaderboard_rows).sort_values('cv_mae')
    return best_estimator, scaler, best_predictions, metrics, leaderboard_df


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
    X = prepare_feature_matrix(data[sleep_features])
    
    results = {}
    all_leaderboards = []
    
    # Build models for each brain biomarker
    for biomarker in brain_biomarkers:
        logger.info(f"\n[Biomarker: {biomarker}]")
        
        y = data[biomarker].fillna(data[biomarker].median())
        
        # Build model
        model, scaler, predictions, metrics, leaderboard = build_brain_aging_model(
            X, y, model_type='auto'
        )
        
        results[biomarker] = {
            'model': model,
            'scaler': scaler,
            'predictions': predictions,
            'metrics': metrics,
            'model_leaderboard': leaderboard
        }
        leaderboard_with_target = leaderboard.copy()
        leaderboard_with_target['biomarker'] = biomarker
        all_leaderboards.append(leaderboard_with_target)
        
        # Feature importance
        if hasattr(model, 'coef_'):
            feature_importance = pd.DataFrame({
                'feature': sleep_features,
                'coefficient': model.coef_,
                'abs_coefficient': np.abs(model.coef_)
            }).sort_values('abs_coefficient', ascending=False)
        elif hasattr(model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': sleep_features,
                'coefficient': model.feature_importances_,
                'abs_coefficient': np.abs(model.feature_importances_)
            }).sort_values('abs_coefficient', ascending=False)
        else:
            feature_importance = None

        if feature_importance is not None:
            
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

    if all_leaderboards:
        leaderboard_df = pd.concat(all_leaderboards, ignore_index=True)
        leaderboard_df.to_csv('outputs/tables/model_selection_leaderboard.csv', index=False)
    
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
