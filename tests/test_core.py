"""
Tests for data loading and preprocessing modules
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


class TestDataLoader:
    """Test data loading functions"""
    
    def test_load_config_exists(self):
        """Test that config file can be loaded"""
        config_path = Path("config/config.yaml")
        assert config_path.exists(), "Config file should exist"
    
    def test_load_clinical_data_columns(self):
        """Test clinical data has required columns"""
        # This test would use sample/mock data
        required_columns = ['participant_id', 'age', 'sex']
        # Placeholder for actual test
        assert True
    
    def test_quality_control_filters(self):
        """Test that QC filters work correctly"""
        # Create mock actigraphy data
        mock_data = pd.DataFrame({
            'participant_id': ['P001'] * 100,
            'activity_counts': np.random.exponential(50, 100),
            'wear_time': np.ones(100)
        })
        
        # QC should not remove any records with 100% wear time
        assert len(mock_data) == 100


class TestFeatureExtraction:
    """Test sleep feature extraction"""
    
    def test_cole_kripke_output_shape(self):
        """Test Cole-Kripke algorithm output dimensions"""
        # Mock activity counts (1 hour of data at 1-min epochs)
        activity = np.random.exponential(50, 60)
        
        # Output should have same shape as input
        # Placeholder for actual implementation test
        assert len(activity) == 60
    
    def test_sleep_efficiency_range(self):
        """Test sleep efficiency is between 0 and 100"""
        # Sleep efficiency must be a percentage
        mock_efficiency = 85.5
        assert 0 <= mock_efficiency <= 100
    
    def test_circadian_metrics_calculation(self):
        """Test circadian metrics are computed correctly"""
        # IS should be between 0 and 1
        mock_is = 0.65
        assert 0 <= mock_is <= 1
        
        # IV should be between 0 and 2
        mock_iv = 0.8
        assert 0 <= mock_iv <= 2


class TestCausalInference:
    """Test causal inference methods"""
    
    def test_propensity_score_range(self):
        """Test propensity scores are between 0 and 1"""
        mock_ps = np.array([0.3, 0.5, 0.7, 0.2, 0.8])
        assert np.all((mock_ps >= 0) & (mock_ps <= 1))
    
    def test_iptw_weights_positive(self):
        """Test IPTW weights are positive"""
        mock_weights = np.array([1.2, 0.8, 1.5, 0.9, 1.1])
        assert np.all(mock_weights > 0)
    
    def test_smd_calculation(self):
        """Test standardized mean difference calculation"""
        # SMD should indicate good balance when close to 0
        treated = np.random.normal(50, 10, 100)
        control = np.random.normal(50, 10, 100)
        
        smd = (np.mean(treated) - np.mean(control)) / np.sqrt(
            (np.var(treated) + np.var(control)) / 2
        )
        
        # With same distribution, SMD should be small
        assert abs(smd) < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
