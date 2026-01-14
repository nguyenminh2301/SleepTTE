"""
Visualization utility functions
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'


def plot_love_plot(
    balance_df: pd.DataFrame,
    output_path: Optional[str] = None,
    threshold: float = 0.1
) -> go.Figure:
    """
    Create Love plot for covariate balance assessment
    
    Args:
        balance_df: DataFrame with SMD values (from assess_covariate_balance)
        output_path: Optional path to save figure
        threshold: SMD threshold for balance
    
    Returns:
        Plotly figure object
    """
    logger.info("Creating Love plot")
    
    fig = go.Figure()
    
    # Unweighted SMD
    fig.add_trace(go.Scatter(
        x=balance_df['smd_unweighted'],
        y=balance_df['covariate'],
        mode='markers',
        name='Unweighted',
        marker=dict(size=10, color='red', symbol='circle')
    ))
    
    # Weighted SMD
    fig.add_trace(go.Scatter(
        x=balance_df['smd_weighted'],
        y=balance_df['covariate'],
        mode='markers',
        name='Weighted (IPTW)',
        marker=dict(size=10, color='blue', symbol='diamond')
    ))
    
    # Add threshold lines
    fig.add_vline(x=threshold, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=-threshold, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_color="black", line_width=1)
    
    fig.update_layout(
        title="Covariate Balance: Love Plot",
        xaxis_title="Standardized Mean Difference",
        yaxis_title="Covariate",
        height=max(400, len(balance_df) * 20),
        showlegend=True,
        template="plotly_white"
    )
    
    if output_path:
        fig.write_image(output_path)
        logger.info(f"Love plot saved to {output_path}")
    
    return fig


def plot_forest_plot(
    results_df: pd.DataFrame,
    estimate_col: str = 'ate',
    ci_lower_col: str = 'ci_lower',
    ci_upper_col: str = 'ci_upper',
    group_col: str = 'intervention',
    output_path: Optional[str] = None
) -> go.Figure:
    """
    Create forest plot for treatment effects
    
    Args:
        results_df: DataFrame with effect estimates and CIs
        estimate_col: Column name for point estimates
        ci_lower_col: Column name for CI lower bounds
        ci_upper_col: Column name for CI upper bounds
        group_col: Column name for grouping variable
        output_path: Optional path to save figure
    
    Returns:
        Plotly figure object
    """
    logger.info("Creating forest plot")
    
    fig = go.Figure()
    
    # Add error bars
    for idx, row in results_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row[estimate_col]],
            y=[row[group_col]],
            error_x=dict(
                type='data',
                symmetric=False,
                array=[row[ci_upper_col] - row[estimate_col]],
                arrayminus=[row[estimate_col] - row[ci_lower_col]]
            ),
            mode='markers',
            marker=dict(size=12, color='darkblue'),
            name=row[group_col],
            showlegend=False
        ))
    
    # Add null line
    fig.add_vline(x=0, line_dash="dash", line_color="red", line_width=2)
    
    fig.update_layout(
        title="Treatment Effects: Forest Plot",
        xaxis_title="Average Treatment Effect (95% CI)",
        yaxis_title="Intervention",
        height=max(400, len(results_df) * 60),
        template="plotly_white"
    )
    
    if output_path:
        fig.write_image(output_path)
        logger.info(f"Forest plot saved to {output_path}")
    
    return fig


def plot_sleep_brain_heatmap(
    correlation_matrix: pd.DataFrame,
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Create heatmap of sleep-brain aging correlations
    
    Args:
        correlation_matrix: Correlation matrix
        output_path: Optional path to save figure
    
    Returns:
        Matplotlib figure object
    """
    logger.info("Creating sleep-brain correlation heatmap")
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    sns.heatmap(
        correlation_matrix,
        annot=True,
        fmt='.2f',
        cmap='RdBu_r',
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        ax=ax
    )
    
    ax.set_title("Sleep Features vs. Brain Aging Biomarkers", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Heatmap saved to {output_path}")
    
    return fig


def plot_cumulative_incidence(
    data: pd.DataFrame,
    time_col: str,
    event_col: str,
    group_col: str,
    output_path: Optional[str] = None
) -> go.Figure:
    """
    Create cumulative incidence curves for CU→MCI progression
    
    Args:
        data: Survival data
        time_col: Time to event column
        event_col: Event indicator column
        group_col: Grouping variable (e.g., treatment)
        output_path: Optional path to save figure
    
    Returns:
        Plotly figure object
    """
    logger.info("Creating cumulative incidence curves")
    
    fig = go.Figure()
    
    groups = data[group_col].unique()
    colors = px.colors.qualitative.Set2
    
    for i, group in enumerate(groups):
        group_data = data[data[group_col] == group].copy()
        group_data = group_data.sort_values(time_col)
        
        # Calculate Kaplan-Meier estimate
        # Simplified version - for production, use lifelines library
        times = group_data[time_col].values
        events = group_data[event_col].values
        
        # Cumulative incidence (1 - survival)
        # This is a placeholder - implement proper KM estimator
        cumulative_incidence = np.cumsum(events) / len(events)
        
        fig.add_trace(go.Scatter(
            x=times,
            y=cumulative_incidence,
            mode='lines',
            name=f'{group_col}={group}',
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    
    fig.update_layout(
        title="Cumulative Incidence of MCI Progression",
        xaxis_title="Time (months)",
        yaxis_title="Cumulative Incidence",
        template="plotly_white",
        height=500
    )
    
    if output_path:
        fig.write_image(output_path)
        logger.info(f"Cumulative incidence plot saved to {output_path}")
    
    return fig


def plot_feature_importance(
    feature_names: List[str],
    importance_values: np.ndarray,
    output_path: Optional[str] = None,
    top_n: int = 20
) -> go.Figure:
    """
    Plot feature importance for sleep-brain aging models
    
    Args:
        feature_names: List of feature names
        importance_values: Array of importance values
        output_path: Optional path to save figure
        top_n: Number of top features to display
    
    Returns:
        Plotly figure object
    """
    logger.info("Creating feature importance plot")
    
    # Create DataFrame and sort
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance_values
    }).sort_values('importance', ascending=False).head(top_n)
    
    fig = go.Figure(go.Bar(
        x=importance_df['importance'],
        y=importance_df['feature'],
        orientation='h',
        marker=dict(color='steelblue')
    ))
    
    fig.update_layout(
        title=f"Top {top_n} Feature Importance",
        xaxis_title="Importance Score",
        yaxis_title="Feature",
        height=max(400, top_n * 25),
        template="plotly_white"
    )
    
    if output_path:
        fig.write_image(output_path)
        logger.info(f"Feature importance plot saved to {output_path}")
    
    return fig


def create_dashboard_layout(
    figures: Dict[str, go.Figure],
    title: str = "Sleep-Brain Aging Analysis Dashboard"
) -> go.Figure:
    """
    Create multi-panel dashboard with multiple figures
    
    Args:
        figures: Dictionary of figure names and plotly figures
        title: Dashboard title
    
    Returns:
        Combined plotly figure
    """
    logger.info("Creating dashboard layout")
    
    n_figs = len(figures)
    rows = (n_figs + 1) // 2
    cols = 2
    
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=list(figures.keys()),
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    for idx, (name, subfig) in enumerate(figures.items()):
        row = (idx // cols) + 1
        col = (idx % cols) + 1
        
        for trace in subfig.data:
            fig.add_trace(trace, row=row, col=col)
    
    fig.update_layout(
        title_text=title,
        height=400 * rows,
        showlegend=True,
        template="plotly_white"
    )
    
    return fig
